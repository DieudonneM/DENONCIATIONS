from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.models import Employeur, Province
from denunciations.models import Incident, MobileDeviceToken


class PublicDeviceTokenApiTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(nom='Kinshasa', code='KIN')
        self.employeur = Employeur.objects.create(
            nom='Societe Test',
            secteur='services',
            province=self.province,
        )
        self.incident = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Description test',
            est_anonyme=True,
        )

    def test_register_device_token_with_code(self):
        url = reverse('api:public_device_token_register')
        payload = {
            'token': 'tok_123',
            'platform': 'android',
            'code_suivi': self.incident.code_suivi,
        }

        response = self.client.post(url, data=payload, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(MobileDeviceToken.objects.count(), 1)

        saved = MobileDeviceToken.objects.get(token='tok_123')
        self.assertEqual(saved.code_suivi, self.incident.code_suivi)
        self.assertEqual(saved.incident_id, self.incident.id)
        self.assertTrue(saved.is_active)

    def test_register_device_token_updates_existing(self):
        MobileDeviceToken.objects.create(token='tok_123', platform='android')
        url = reverse('api:public_device_token_register')

        response = self.client.post(
            url,
            data={
                'token': 'tok_123',
                'platform': 'ios',
                'code_suivi': self.incident.code_suivi,
            },
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MobileDeviceToken.objects.count(), 1)

        saved = MobileDeviceToken.objects.get(token='tok_123')
        self.assertEqual(saved.platform, 'ios')
        self.assertEqual(saved.code_suivi, self.incident.code_suivi)


class StatusChangePushSignalTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(nom='Kongo Central', code='KON')
        self.employeur = Employeur.objects.create(
            nom='Entreprise Signal',
            secteur='services',
            province=self.province,
        )
        self.incident = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Matadi',
            type_incident='salaire',
            description='Description signal',
            est_anonyme=True,
            statut='nouvelle',
        )

    def test_status_change_triggers_push_service(self):
        with patch('core.signals.send_incident_status_change_push') as mocked_sender:
            with self.captureOnCommitCallbacks(execute=True):
                self.incident.statut = 'analyse'
                self.incident.save()

        mocked_sender.assert_called_once()
        kwargs = mocked_sender.call_args.kwargs
        self.assertEqual(kwargs['incident'].id, self.incident.id)
        self.assertEqual(kwargs['old_status'], 'nouvelle')
        self.assertEqual(kwargs['new_status'], 'analyse')
