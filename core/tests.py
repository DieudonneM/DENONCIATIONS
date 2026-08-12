"""
Tests pour les modèles et fonctionnalités de base.
"""

import tempfile
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from core.models import Province, Employeur
from core.views import _repair_cloudinary_url
from denunciations.models import Incident, Commentaire, PieceJointe

User = get_user_model()


class UserModelTest(TestCase):
    """Tests pour le modèle User personnalisé."""
    
    def setUp(self):
        self.province = Province.objects.create(
            nom='Test Province',
            code='TST'
        )

    def test_delete_account_deletes_authenticated_user(self):
        user = User.objects.create_user(
            username='delete_user_test',
            email='delete-user@test.cd',
            password='password123',
            role='travailleur',
            first_name='Claire',
            last_name='Test'
        )
        self.client.force_login(user)

        response = self.client.delete(reverse('api:delete_user_account'))

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(user.email.endswith('@test.cd'))

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


class StaffNouvellesApiTest(TestCase):
    """Tests du flux mobile staff pour la liste des dénonciations nouvelles."""

    def setUp(self):
        self.province = Province.objects.create(nom='Kinshasa', code='KIN')
        self.employeur = Employeur.objects.create(
            nom='Entreprise Dashboard',
            secteur='services',
            province=self.province,
            ville='Kinshasa',
        )
        self.agent = User.objects.create_user(
            username='agent_staff_dashboard',
            email='agent_staff_dashboard@test.cd',
            password='password123',
            role='agent',
            first_name='Marie',
            last_name='Kalonda',
        )
        self.agent.provinces.add(self.province)

        self.travailleur = User.objects.create_user(
            username='travailleur_dashboard',
            email='travailleur_dashboard@test.cd',
            password='password123',
            role='travailleur',
        )

    def _auth_headers(self, user):
        return {'HTTP_AUTHORIZATION': f'Bearer session-{user.id}'}

    def test_requires_authentication(self):
        response = self.client.get('/api/incidents/staff-nouvelles/')
        self.assertEqual(response.status_code, 401)

    def test_forbidden_for_non_staff(self):
        response = self.client.get(
            '/api/incidents/staff-nouvelles/',
            **self._auth_headers(self.travailleur),
        )
        self.assertEqual(response.status_code, 403)

    def test_returns_only_nouvelle_ordered_desc_with_pagination(self):
        for idx in range(12):
            Incident.objects.create(
                employeur=self.employeur,
                province=self.province,
                ville='Kinshasa',
                type_incident='salaire',
                description=f'Incident nouvelle #{idx}',
                statut='nouvelle',
                est_anonyme=True,
            )

        Incident.objects.create(
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Incident analyse ignore',
            statut='analyse',
            est_anonyme=True,
        )

        page1 = self.client.get(
            '/api/incidents/staff-nouvelles/?page=1',
            **self._auth_headers(self.agent),
        )
        self.assertEqual(page1.status_code, 200)
        body1 = page1.json()
        self.assertEqual(body1.get('page'), 1)
        self.assertEqual(body1.get('page_size'), 10)
        self.assertEqual(body1.get('total'), 12)
        self.assertTrue(body1.get('has_next'))

        rows1 = body1.get('results', [])
        self.assertEqual(len(rows1), 10)
        for row in rows1:
            self.assertEqual(row.get('statut'), 'nouvelle')

        dates_page1 = [row.get('date_creation') for row in rows1]
        self.assertEqual(dates_page1, sorted(dates_page1, reverse=True))

        page2 = self.client.get(
            '/api/incidents/staff-nouvelles/?page=2',
            **self._auth_headers(self.agent),
        )
        self.assertEqual(page2.status_code, 200)
        body2 = page2.json()
        self.assertEqual(body2.get('page'), 2)
        self.assertFalse(body2.get('has_next'))
        self.assertEqual(len(body2.get('results', [])), 2)


class PieceJointeDownloadViewTest(TestCase):
    """Tests de l’endpoint de téléchargement des pièces jointes."""

    def test_repair_cloudinary_url_for_documents(self):
        url = 'https://res.cloudinary.com/demo/image/upload/v123/attachments/test.pdf'
        repaired = _repair_cloudinary_url(url, 'test.pdf')
        self.assertIn('/raw/upload/', repaired)
        self.assertIn('test.pdf', repaired)

    def test_repair_cloudinary_url_for_audio_files(self):
        url = 'https://res.cloudinary.com/demo/image/upload/v123/attachments/test.mp3'
        repaired = _repair_cloudinary_url(url, 'test.mp3')
        self.assertIn('/video/upload/', repaired)
        self.assertIn('test.mp3', repaired)

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_download_attachment_serves_file(self):
        province = Province.objects.create(nom='Province Test', code='PRT')
        employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='industrie',
            province=province,
            ville='Kinshasa',
        )
        incident = Incident.objects.create(
            employeur=employeur,
            province=province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Test téléchargement',
            est_anonyme=False,
        )
        piece = PieceJointe.objects.create(
            incident=incident,
            fichier=SimpleUploadedFile('test.pdf', b'pdf-content', content_type='application/pdf'),
            nom_original='test.pdf',
            type_fichier='application/pdf',
            taille_fichier=11,
        )

        response = self.client.get(reverse('core:attachment_download', kwargs={'pk': piece.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'pdf-content')
        self.assertIn('inline; filename="test.pdf"', response['Content-Disposition'])

    @override_settings(
        DEBUG=False,
        CLOUDINARY_STORAGE={'CLOUD_NAME': 'demo', 'API_KEY': 'key', 'API_SECRET': 'secret'},
    )
    @patch('core.views._verify_remote_file_url', return_value=True)
    def test_download_attachment_redirects_to_cloudinary_when_local_url_is_invalid(self, _mock_verify):
        province = Province.objects.create(nom='Province Test', code='PRT')
        employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='industrie',
            province=province,
            ville='Kinshasa',
        )
        incident = Incident.objects.create(
            employeur=employeur,
            province=province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Test redirection Cloudinary',
            est_anonyme=False,
        )
        piece = PieceJointe.objects.create(
            incident=incident,
            fichier='VigiTravail/documents/incidents/2026/07/23/test.pdf',
            nom_original='test.pdf',
            type_fichier='application/pdf',
            taille_fichier=11,
        )

        response = self.client.get(reverse('core:attachment_download', kwargs={'pk': piece.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            'https://res.cloudinary.com/demo/raw/upload/v1/VigiTravail/documents/incidents/2026/07/23/test.pdf',
        )


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
