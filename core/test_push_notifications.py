from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.models import Employeur, Province
from denunciations.models import Commentaire, Incident, MobileDeviceToken
from users.models import User


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

    def test_register_device_token_staff_subscription(self):
        url = reverse('api:public_device_token_register')
        payload = {
            'token': 'tok_staff_1',
            'platform': 'android',
            'user_role': 'agent',
            'receives_staff_notifications': True,
        }

        response = self.client.post(url, data=payload, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        saved = MobileDeviceToken.objects.get(token='tok_staff_1')
        self.assertEqual(saved.user_role, 'agent')
        self.assertTrue(saved.receives_staff_notifications)


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


class CommentairePushSignalTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(nom='Kongo Central', code='KON')
        self.employeur = Employeur.objects.create(
            nom='Entreprise Commentaire',
            secteur='services',
            province=self.province,
        )
        self.incident = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Matadi',
            type_incident='salaire',
            description='Description commentaire',
            est_anonyme=True,
            statut='analyse',
        )

    def test_commentaire_public_ministere_triggers_push_service(self):
        with patch('core.signals.send_incident_comment_push') as mocked_sender:
            with self.captureOnCommitCallbacks(execute=True):
                Commentaire.objects.create(
                    incident=self.incident,
                    texte='Commentaire de suivi',
                    type_commentaire='public',
                    origine_public='ministere',
                )

        mocked_sender.assert_called_once()
        kwargs = mocked_sender.call_args.kwargs
        self.assertEqual(kwargs['incident'].id, self.incident.id)
        self.assertEqual(kwargs['commentaire'].texte, 'Commentaire de suivi')


class StaffPushSignalTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(nom='Bas-Uele', code='BAS')
        self.employeur = Employeur.objects.create(
            nom='Entreprise Staff',
            secteur='services',
            province=self.province,
        )

    def test_incident_created_triggers_staff_push_service(self):
        with patch('core.signals.send_staff_incident_created_push') as mocked_sender:
            with self.captureOnCommitCallbacks(execute=True):
                Incident.objects.create(
                    employeur=self.employeur,
                    province=self.province,
                    ville='Buta',
                    type_incident='salaire',
                    description='Nouveau cas',
                    est_anonyme=True,
                )

        mocked_sender.assert_called_once()
        kwargs = mocked_sender.call_args.kwargs
        self.assertEqual(kwargs['incident'].ville, 'Buta')

    def test_denonciateur_public_comment_triggers_staff_push_service(self):
        incident = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Buta',
            type_incident='salaire',
            description='Cas suivi',
            est_anonyme=True,
            statut='analyse',
        )

        travailleur = User.objects.create_user(
            username='travailleur.staff',
            email='travailleur.staff@example.com',
            password='password123',
            role='travailleur',
        )

        with patch('core.signals.send_staff_denonciateur_reply_push') as mocked_sender:
            with self.captureOnCommitCallbacks(execute=True):
                Commentaire.objects.create(
                    incident=incident,
                    auteur=travailleur,
                    texte='Merci pour votre retour.',
                    type_commentaire='public',
                    origine_public='denonciateur',
                )

        mocked_sender.assert_called_once()
        kwargs = mocked_sender.call_args.kwargs
        self.assertEqual(kwargs['incident'].id, incident.id)
        self.assertEqual(kwargs['commentaire'].origine_public, 'denonciateur')
