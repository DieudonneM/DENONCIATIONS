from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import load_workbook

from core.models import Employeur, Province
from users.models import User
from .models import Incident


@override_settings(ALLOWED_HOSTS=['testserver'])
class LegacyRouteRedirectTests(TestCase):
    def test_legacy_incidents_url_redirects_to_core_namespace(self):
        response = self.client.get(reverse('denunciations:incidents_list'))

        self.assertRedirects(
            response,
            reverse('core:incidents_list'),
            status_code=307,
            target_status_code=200,
            fetch_redirect_response=False,
        )

    def test_legacy_form_post_preserves_request_method(self):
        response = self.client.post(reverse('denunciations:incident_form'))

        self.assertEqual(response.status_code, 307)
        self.assertEqual(response['Location'], reverse('core:incident_form'))


@override_settings(ALLOWED_HOSTS=['testserver'])
class IncidentExportAuthorizationTests(TestCase):
    def test_worker_export_excludes_incidents_owned_by_other_workers(self):
        province = Province.objects.create(nom='Kinshasa', code='KIN')
        employeur = Employeur.objects.create(
            nom='Entreprise privée',
            secteur='services',
            province=province,
        )
        owner = User.objects.create_user(
            username='owner',
            email='owner@example.test',
            password='safe-password',
            role='travailleur',
        )
        other_worker = User.objects.create_user(
            username='other-worker',
            email='other@example.test',
            password='safe-password',
            role='travailleur',
        )
        private_incident = Incident.objects.create(
            code_suivi='RDC2026PRIVATE',
            travailleur=owner,
            employeur=employeur,
            province=province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Incident confidentiel appartenant à un autre travailleur.',
        )

        self.client.force_login(other_worker)
        response = self.client.get(reverse('core:export_incidents_xlsx'))

        self.assertEqual(response.status_code, 200)
        workbook = load_workbook(BytesIO(response.content))
        values = [
            value
            for row in workbook.active.iter_rows(values_only=True)
            for value in row
            if value is not None
        ]
        self.assertNotIn(private_incident.code_suivi, values)
        self.assertNotIn(private_incident.description, values)


class PublicIncidentAttachmentTests(TestCase):
    def test_public_incident_accepts_allowed_attachments(self):
        province = Province.objects.create(nom='Kinshasa', code='KIN')
        Employeur.objects.create(
            nom='Entreprise privée',
            secteur='services',
            province=province,
        )

        payload = {
            'employeur': 'Entreprise privée',
            'employeur_address': '123 Rue',
            'ville': 'Kinshasa',
            'province': province.id,
            'type_incident': 'salaire',
            'description': 'Description suffisante pour le test de pièces jointes.',
            'le_fautif': 'Entreprise privée',
            'est_anonyme': True,
            'email_contact_anonyme': 'test@example.com',
            'telephone_contact_anonyme': '',
            'secteur': 'services',
            'autre_secteur': '',
            'confirm_anonymous': True,
        }
        response = self.client.post(
            reverse('api:public_incident_create'),
            payload,
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)

    def test_public_incident_accepts_non_existing_province_name(self):
        payload = {
            'employeur': 'Entreprise privée',
            'employeur_address': '123 Rue',
            'ville': 'Kinshasa',
            'province': 'Bas-Uélé',
            'type_incident': 'salaire',
            'description': 'Description suffisante pour valider le choix d’une province non encore créée.',
            'le_fautif': 'Entreprise privée',
            'est_anonyme': True,
            'email_contact_anonyme': 'test@example.com',
            'telephone_contact_anonyme': '',
            'secteur': 'services',
            'autre_secteur': '',
            'confirm_anonymous': True,
        }

        response = self.client.post(
            reverse('api:public_incident_create'),
            payload,
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Province.objects.filter(nom__iexact='Bas-Uélé').exists())