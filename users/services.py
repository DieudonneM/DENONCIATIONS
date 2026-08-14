from datetime import timedelta

from django.utils import timezone
from django.utils.crypto import get_random_string


TEMPORARY_PASSWORD_TTL = timedelta(minutes=5)
TEMPORARY_PASSWORD_ALPHABET = (
    'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
)


def reset_to_temporary_password(user):
    temporary_password = get_random_string(
        12,
        allowed_chars=TEMPORARY_PASSWORD_ALPHABET,
    )
    user.set_password(temporary_password)
    user.must_change_password = True
    user.temp_password_set_at = timezone.now()
    user.temp_password_used_at = None
    user.save(update_fields=[
        'password',
        'must_change_password',
        'temp_password_set_at',
        'temp_password_used_at',
    ])
    return temporary_password