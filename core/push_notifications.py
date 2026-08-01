"""Services de notification push (FCM)."""

import json
import logging
from typing import Optional

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from denunciations.models import Incident, MobileDeviceToken

logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except Exception:  # pragma: no cover - handled by graceful runtime checks
    firebase_admin = None
    credentials = None
    messaging = None


def _get_firebase_app():
    """Initialise Firebase Admin si configuré, sinon retourne None."""
    if firebase_admin is None or credentials is None:
        return None

    if firebase_admin._apps:
        return firebase_admin.get_app()

    creds_path = str(getattr(settings, 'FIREBASE_CREDENTIALS_FILE', '') or '').strip()
    creds_json = str(getattr(settings, 'FIREBASE_CREDENTIALS_JSON', '') or '').strip()

    if not creds_path and not creds_json:
        return None

    try:
        if creds_json:
            cert_data = json.loads(creds_json)
            cert = credentials.Certificate(cert_data)
        else:
            cert = credentials.Certificate(creds_path)
        return firebase_admin.initialize_app(cert)
    except Exception:
        logger.exception('Impossible d\'initialiser Firebase Admin.')
        return None


def _status_label(raw: str) -> str:
    mapping = {
        'nouvelle': 'Nouvelle',
        'analyse': 'En cours d\'analyse',
        'attente': 'En attente d\'informations',
        'resolue': 'Resolue',
        'classée': 'Classee sans suite',
    }
    return mapping.get(raw, raw)


def send_incident_status_change_push(
    *,
    incident: Incident,
    old_status: str,
    new_status: str,
) -> dict:
    """Envoie une push FCM aux tokens concernés par un incident."""
    app = _get_firebase_app()
    if app is None or messaging is None:
        return {'sent': 0, 'failed': 0, 'reason': 'firebase_not_configured'}

    token_rows = list(
        MobileDeviceToken.objects.filter(is_active=True)
        .filter(Q(incident=incident) | Q(code_suivi=incident.code_suivi))
        .exclude(token='')
        .values_list('id', 'token')
        .distinct()
    )

    if not token_rows:
        return {'sent': 0, 'failed': 0, 'reason': 'no_tokens'}

    token_ids = [row[0] for row in token_rows]
    tokens = [row[1] for row in token_rows]

    title = 'Mise a jour de votre denonciation'
    body = (
        f'Le dossier {incident.code_suivi} est passe de '
        f'{_status_label(old_status)} a {_status_label(new_status)}.'
    )

    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data={
            'type': 'incident_status_changed',
            'code_suivi': incident.code_suivi,
            'old_status': old_status,
            'new_status': new_status,
        },
    )

    try:
        response = messaging.send_each_for_multicast(message, app=app)
    except Exception:
        logger.exception('Echec d\'envoi push pour incident=%s', incident.code_suivi)
        MobileDeviceToken.objects.filter(id__in=token_ids).update(
            last_error='fcm_send_exception',
        )
        return {'sent': 0, 'failed': len(tokens), 'reason': 'send_exception'}

    sent_ids = []
    failed_items = []

    for idx, item in enumerate(response.responses):
        token_id = token_ids[idx]
        token = tokens[idx]

        if item.success:
            sent_ids.append(token_id)
            continue

        code = ''
        if item.exception is not None:
            code = getattr(item.exception, 'code', '') or getattr(item.exception, 'message', '') or str(item.exception)

        failed_items.append((token_id, token, str(code)))

    now = timezone.now()
    if sent_ids:
        MobileDeviceToken.objects.filter(id__in=sent_ids).update(
            last_notified_at=now,
            last_error='',
        )

    deactivate_codes = {
        'registration-token-not-registered',
        'invalid-argument',
    }

    for token_id, _, error_code in failed_items:
        should_deactivate = any(code in error_code for code in deactivate_codes)
        MobileDeviceToken.objects.filter(id=token_id).update(
            is_active=False if should_deactivate else True,
            last_error=error_code[:500],
        )

    return {
        'sent': len(sent_ids),
        'failed': len(failed_items),
        'reason': 'ok',
    }
