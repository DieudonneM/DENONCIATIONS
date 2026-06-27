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

    def test_agent_dashboard_stat_cards_link_to_filtered_incidents_page(self):
        """Le dashboard agent doit rediriger vers la page de publications filtrée lorsqu'on clique sur une statistique."""
        province = Province.objects.create(nom='Province Test', code='PST')
        user = User.objects.create_user(
            username='agent_dashboard_link',
            email='agent_dashboard_link@test.cd',
            password='password123',
            role='agent'
        )
        user.provinces.add(province)
        self.client.force_login(user)

        response = self.client.get(reverse('core:dashboard_agent'))

        self.assertContains(
            response,
            f'href="{reverse("denunciations:incidents_list")}?statut=nouvelle"'
        )

    def test_incidents_list_heading_reflects_status_filter(self):
        """La page de liste doit afficher un titre explicite quand un filtre de statut est appliqué."""
        user = User.objects.create_user(
            username='travailleur_heading',
            email='travailleur_heading@test.cd',
            password='password123',
            role='travailleur'
        )
        self.client.force_login(user)

        response = self.client.get(reverse('denunciations:incidents_list'), {'statut': 'nouvelle'})

        self.assertContains(response, 'Dénonciations nouvelles')


class AdminManagementTest(TestCase):
    """Tests des actions d'administration personnalisées."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_management',
            email='admin_management@test.cd',
            password='password123',
            role='administrateur'
        )
        self.province = Province.objects.create(nom='Kinshasa', code='KIN')
        self.employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='industrie',
            province=self.province,
            ville='Kinshasa'
        )
        self.user = User.objects.create_user(
            username='travailleur_admin',
            email='travailleur_admin@test.cd',
            password='password123',
            role='travailleur'
        )
        self.incident = Incident.objects.create(
            travailleur=self.user,
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Incident de test'
        )

    def test_admin_root_redirects_to_dashboard(self):
        """La racine admin doit rediriger vers le dashboard statistique."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('core:admin_root'))
        self.assertRedirects(response, reverse('core:admin_dashboard'))

    def test_admin_dashboard_renders_charts(self):
        """Le dashboard admin doit afficher les graphiques de synthèse."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('core:admin_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="evolutionChart"')
        self.assertContains(response, 'id="typeChart"')
        self.assertContains(response, 'id="repartitionChart"')
        self.assertContains(response, 'id="provinceChart"')
        self.assertContains(response, 'id="sectorChart"')
        self.assertContains(response, 'Réinitialiser les filtres')
        self.assertContains(response, 'Non lues')
        self.assertContains(response, 'Archivé')
        self.assertNotContains(response, 'Répartition détaillée')

    def test_admin_can_reset_user_password(self):
        """L'admin doit pouvoir réinitialiser le mot de passe d'un utilisateur."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('core:admin_users_reset_password', kwargs={'user_id': self.user.id}),
            follow=True
        )
        self.assertRedirects(response, reverse('core:admin_users_list'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('ChangeMe123!'))

    def test_admin_can_delete_incident(self):
        """L'admin doit pouvoir supprimer une publication."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('core:admin_incidents_delete', kwargs={'incident_id': self.incident.id}),
            follow=True
        )
        self.assertRedirects(response, reverse('core:admin_incidents_list'))
        self.assertFalse(Incident.objects.filter(pk=self.incident.pk).exists())


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


class IncidentDetailPermissionsTest(TestCase):
    """Tests de permissions et d'affichage des détails d'un incident."""

    def setUp(self):
        self.province = Province.objects.create(nom='Test Province', code='TST')
        self.employeur = Employeur.objects.create(
            nom='Entreprise Test',
            secteur='industrie',
            province=self.province,
            ville='Kinshasa'
        )
        self.travailleur = User.objects.create_user(
            username='travailleur_edit',
            email='travailleur_edit@test.cd',
            password='password123',
            role='travailleur'
        )
        self.agent = User.objects.create_user(
            username='agent_comment_view',
            email='agent_comment_view@test.cd',
            password='password123',
            role='agent'
        )
        self.agent.provinces.add(self.province)

    def test_travailleur_can_edit_own_incident(self):
        """Le dénonciateur doit pouvoir modifier sa propre publication."""
        incident = Incident.objects.create(
            travailleur=self.travailleur,
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Description initiale',
            est_anonyme=False
        )

        self.client.force_login(self.travailleur)
        response = self.client.get(reverse('core:incident_edit', kwargs={'code': incident.code_suivi}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Description initiale')

        response = self.client.post(
            reverse('core:incident_edit', kwargs={'code': incident.code_suivi}),
            {
                'type_incident': 'salaire',
                'ville': 'Lubumbashi',
                'province': self.province.id,
                'description': 'Description modifiée',
                'employeur': 'Entreprise Test',
                'email_contact_anonyme': '',
                'telephone_contact_anonyme': '',
                'est_anonyme': 'on',
                'le_fautif': '',
            },
            follow=True
        )

        incident.refresh_from_db()
        self.assertEqual(incident.description, 'Description modifiée')
        self.assertEqual(incident.ville, 'Lubumbashi')
        self.assertTrue(incident.est_anonyme)
        self.assertRedirects(response, reverse('core:incident_detail', kwargs={'code': incident.code_suivi}))

    def test_detail_view_shows_all_comments_to_travailleur(self):
        """Le dénonciateur doit voir tous les commentaires, y compris internes."""
        incident = Incident.objects.create(
            travailleur=self.travailleur,
            employeur=self.employeur,
            province=self.province,
            ville='Kinshasa',
            type_incident='salaire',
            description='Incident test',
            est_anonyme=False
        )
        Commentaire.objects.create(
            incident=incident,
            auteur=self.agent,
            texte='Commentaire interne',
            type_commentaire='interne'
        )
        Commentaire.objects.create(
            incident=incident,
            auteur=self.agent,
            texte='Commentaire public',
            type_commentaire='public'
        )

        self.client.force_login(self.travailleur)
        response = self.client.get(reverse('core:incident_detail', kwargs={'code': incident.code_suivi}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Commentaire interne')
        self.assertContains(response, 'Commentaire public')
