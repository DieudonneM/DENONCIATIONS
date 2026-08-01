from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail

from core.models import Province, Employeur
from denunciations.models import Incident
from users.models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class IncidentNotificationTest(TestCase):
    def setUp(self):
        self.province = Province.objects.create(nom='Kinshasa', code='KIN')
        self.employeur = Employeur.objects.create(
            nom='ACME RDC',
            secteur='services',
            province=self.province,
        )

        self.agent = User.objects.create_user(
            username='agent_test',
            email='agent@example.com',
            password='secret123',
            role='agent',
            is_active=True,
            first_name='Agent',
            last_name='Test',
        )
        self.agent.provinces.add(self.province)

        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@example.com',
            password='secret123',
            role='administrateur',
            is_active=True,
            first_name='Admin',
            last_name='Test',
        )

    def test_new_incident_notifies_active_agents_and_admins(self):
        url = reverse('core:incident_form')
        data = {
            'type_incident': 'salaire',
            'ville': 'Kinshasa',
            'province': str(self.province.id),
            'description': 'Description de test pour la notification.',
            'email_contact_anonyme': 'contact@example.com',
            'telephone_contact_anonyme': '+243812345678',
            'est_anonyme': 'on',
            'confirm_anonymous': 'on',
            'employeur': self.employeur.nom,
            'employeur_address': 'Rue de test 1',
            'secteur': 'services',
            'le_fautif': 'Le fautif de test',
        }

        response = self.client.post(url, data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Incident.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

        sent = mail.outbox[0]
        self.assertIn('Nouvelle dénonciation', sent.subject)
        self.assertIn('agent@example.com', sent.to)
        self.assertIn('admin@example.com', sent.to)
