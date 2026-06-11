"""
Tests pour les modèles et fonctionnalités de base.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from denunciations.models import Province, Employeur, Incident, Commentaire, PieceJointe

User = get_user_model()


class UserModelTest(TestCase):
    """Tests pour le modèle User personnalisé."""
    
    def setUp(self):
        self.province = Province.objects.create(
            nom='Test Province',
            code='TST'
        )
    
    def test_create_travailleur(self):
        """Test de création d'un utilisateur Travailleur."""
        user = User.objects.create_user(
            username='travailleur_case_a',
            email='travailleur_case_a@test.cd',
            password='password123',
            role='travailleur',
            first_name='Jean',
            last_name='Doe'
        )
        self.assertEqual(user.role, 'travailleur')
        self.assertTrue(user.is_active)
    
    def test_create_agent(self):
        """Test de création d'un utilisateur Agent."""
        user = User.objects.create_user(
            username='agent_user_case_b',
            email='agent_user_case_b@test.cd',
            password='password123',
            role='agent'
        )
        user.provinces.add(self.province)
        self.assertEqual(user.role, 'agent')
        self.assertEqual(user.provinces.count(), 1)
    
    def test_create_admin(self):
        """Test de création d'un administrateur."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@test.cd',
            password='password123',
            role='administrateur'
        )
        self.assertEqual(user.role, 'administrateur')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class ProvinceModelTest(TestCase):
    """Tests pour le modèle Province."""
    
    def test_create_province(self):
        """Test de création d'une province."""
        province = Province.objects.create(
            nom='Kinshasa',
            code='KIN',
            description='Capitale de la RDC'
        )
        self.assertEqual(province.nom, 'Kinshasa')
        self.assertEqual(str(province), 'Kinshasa')


class EmployeurModelTest(TestCase):
    """Tests pour le modèle Employeur."""
    
    def setUp(self):
        self.province = Province.objects.create(
            nom='Test Province',
            code='TST'
        )
    
    def test_create_employeur(self):
        """Test de création d'un employeur."""
        employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='industrie',
            province=self.province,
            ville='Kinshasa',
            email='contact@entreprise.cd'
        )
        self.assertEqual(employeur.nom, 'Entreprise Test')
        self.assertEqual(employeur.secteur, 'industrie')


class IncidentModelTest(TestCase):
    """Tests pour le modèle Incident."""
    
    def setUp(self):
        self.province = Province.objects.create(
            nom='Test Province',
            code='TST'
        )
        self.employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='industrie',
            province=self.province,
            ville='Kinshasa'
        )
        self.travailleur = User.objects.create_user(
            username='travailleur_case_incident',
            email='travailleur_case_incident@test.cd',
            password='password123',
            role='travailleur'
        )
        self.agent = User.objects.create_user(
            username='agent_case_incident',
            email='agent_case_incident@test.cd',
            password='password123',
            role='agent'
        )
        self.agent.provinces.add(self.province)
    
    def test_create_incident(self):
        """Test de création d'un incident."""
        incident = Incident.objects.create(
            travailleur=self.travailleur,
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Non-paiement du salaire de 3 mois',
            est_anonyme=False
        )
        self.assertIsNotNone(incident.code_suivi)
        self.assertEqual(incident.statut, 'nouvelle')
        self.assertTrue(incident.code_suivi.startswith('RDC'))
    
    def test_incident_code_suivi_unique(self):
        """Test que le code de suivi est unique."""
        incident1 = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Incident 1'
        )
        incident2 = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Incident 2'
        )
        self.assertNotEqual(incident1.code_suivi, incident2.code_suivi)
    
    def test_incident_anonymous(self):
        """Test la création d'un incident anonyme."""
        incident = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Dénonciation anonyme',
            est_anonyme=True,
            email_contact_anonyme='anonyme@test.cd'
        )
        self.assertTrue(incident.est_anonyme)
        self.assertIsNone(incident.travailleur)

    def test_auto_assign_agent_by_province(self):
        """Test que l'incident est automatiquement assigné à un agent de la province."""
        first_agent = User.objects.create_user(
            username='agent_auto_1',
            email='agent_auto_1@test.cd',
            password='password123',
            role='agent'
        )
        first_agent.provinces.add(self.province)

        second_agent = User.objects.create_user(
            username='agent_auto_2',
            email='agent_auto_2@test.cd',
            password='password123',
            role='agent'
        )
        second_agent.provinces.add(self.province)

        incident = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Non-paiement du salaire de 3 mois',
            est_anonyme=False
        )

        self.assertIsNotNone(incident.agent_assigné)
        assigned_agents = list(User.objects.filter(role='agent', provinces=self.province).distinct())
        self.assertIn(incident.agent_assigné, assigned_agents)


class DashboardAccessTest(TestCase):
    """Tests de sécurité des dashboards."""

    def test_dashboard_agent_requires_login(self):
        """Un utilisateur anonyme ne doit pas déclencher d'erreur sur le dashboard agent."""
        response = self.client.get(reverse('core:dashboard_agent'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])


class CommentaireModelTest(TestCase):
    """Tests pour le modèle Commentaire."""
    
    def setUp(self):
        self.province = Province.objects.create(
            nom='Test Province',
            code='TST'
        )
        self.employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='industrie',
            province=self.province,
            ville='Kinshasa'
        )
        self.incident = Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Test incident'
        )
        self.agent = User.objects.create_user(
            username='agent_commentaire_case',
            email='agent_commentaire_case@test.cd',
            password='password123',
            role='agent'
        )

    def test_create_commentaire_interne(self):
        """Test de création d'un commentaire interne."""
        commentaire = Commentaire.objects.create(
            incident=self.incident,
            auteur=self.agent,
            texte='Commentaire interne pour analyse',
            type_commentaire='interne'
        )
        self.assertEqual(commentaire.type_commentaire, 'interne')
    
    def test_create_commentaire_public(self):
        """Test de création d'un commentaire public."""
        commentaire = Commentaire.objects.create(
            incident=self.incident,
            auteur=self.agent,
            texte='Réponse au travailleur',
            type_commentaire='public'
        )
        self.assertEqual(commentaire.type_commentaire, 'public')
