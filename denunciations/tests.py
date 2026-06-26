from django.test import TestCase
from django.contrib.auth import get_user_model

from denunciations.models import Employeur, Incident, Province
from denunciations.views import IncidentDetailView


class IncidentDetailViewPermissionTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.province = Province.objects.create(nom='Kinshasa', code='KN')
        self.employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='services',
            province=self.province,
        )

        self.travailleur = self.User.objects.create_user(
            username='travailleur1',
            email='travailleur1@example.com',
            password='secret123',
            role='travailleur',
        )
        self.agent = self.User.objects.create_user(
            username='agent1',
            email='agent1@example.com',
            password='secret123',
            role='agent',
        )
        self.admin = self.User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='secret123',
            role='administrateur',
        )
        self.other_travailleur = self.User.objects.create_user(
            username='travailleur2',
            email='travailleur2@example.com',
            password='secret123',
            role='travailleur',
        )

        self.incident = Incident.objects.create(
            travailleur=self.travailleur,
            employeur=self.employeur,
            ville='Kinshasa',
            province=self.province,
            type_incident='salaire',
            description='Description de test',
            est_anonyme=False,
        )

    def test_permission_check_allows_admin_and_agent_and_owner(self):
        self.assertTrue(IncidentDetailView._can_view_incident(self.admin, self.incident))
        self.assertTrue(IncidentDetailView._can_view_incident(self.agent, self.incident))
        self.assertTrue(IncidentDetailView._can_view_incident(self.travailleur, self.incident))
        self.assertFalse(IncidentDetailView._can_view_incident(self.other_travailleur, self.incident))

    def test_detail_view_renders_existing_template_for_authenticated_user(self):
        self.client.force_login(self.admin)
        response = self.client.get(f'/detail/{self.incident.code_suivi}/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/detail_incident.html')
