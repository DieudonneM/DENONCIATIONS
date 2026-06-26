"""
Tests pour les vues d'administration personnalisées dans l'application `core`.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.messages import get_messages

User = get_user_model()


class AdminUserPasswordResetTest(TestCase):
    """
    Tests pour la vue `admin_users_send_reset_link`.
    """

    def setUp(self):
        """
        Configuration initiale pour les tests.
        Crée un administrateur, un agent et un travailleur.
        """
        self.admin_user = User.objects.create_superuser(
            'admin@test.com', 'password123'
        )
        self.test_user = User.objects.create_user(
            'testuser@test.com', 'password123', role='travailleur'
        )
        self.agent_user = User.objects.create_user(
            'agent@test.com', 'password123', role='agent'
        )
        self.url = reverse('core:admin_users_send_reset_link', args=[self.test_user.id])
        self.user_list_url = reverse('core:admin_users_list')

    def test_unauthenticated_user_cannot_send_reset_link(self):
        """Vérifie qu'un utilisateur non connecté est redirigé vers la page de connexion."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('users:login')}?next={self.url}")

    def test_non_admin_user_cannot_send_reset_link(self):
        """Vérifie qu'un utilisateur non-administrateur est redirigé avec un message d'erreur."""
        self.client.login(email='agent@test.com', password='password123')
        response = self.client.post(self.url, follow=True)
        
        self.assertRedirects(response, reverse('core:home'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Accès refusé. Vous devez être administrateur.')

    def test_get_request_is_not_allowed(self):
        """Vérifie que les requêtes GET retournent une erreur 405 (Méthode non autorisée)."""
        self.client.login(email='admin@test.com', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_admin_can_send_reset_link_successfully(self):
        """Vérifie qu'un admin peut déclencher l'envoi d'un email de réinitialisation."""
        self.client.login(email='admin@test.com', password='password123')
        response = self.client.post(self.url)

        # Vérifie qu'un email a été envoyé
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.test_user.email])
        self.assertIn('Réinitialisation du mot de passe', email.subject)
        self.assertIn('password_reset_confirm', email.body)

        # Vérifie le message de succès
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f"Un lien de réinitialisation de mot de passe a été envoyé à {self.test_user.email}.")

        # Vérifie la redirection
        self.assertRedirects(response, self.user_list_url)

    def test_send_reset_link_for_nonexistent_user_returns_404(self):
        """Vérifie qu'une erreur 404 est retournée pour un utilisateur qui n'existe pas."""
        self.client.login(email='admin@test.com', password='password123')
        invalid_url = reverse('core:admin_users_send_reset_link', args=[999])
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_send_reset_link_for_inactive_user_fails_gracefully(self):
        """Vérifie que l'envoi à un utilisateur inactif échoue avec un message d'erreur."""
        self.test_user.is_active = False
        self.test_user.save()

        self.client.login(email='admin@test.com', password='password123')
        response = self.client.post(self.url)

        self.assertEqual(len(mail.outbox), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), f"Impossible d'envoyer l'email de réinitialisation pour {self.test_user.email}. L'utilisateur est-il actif ?")
        self.assertRedirects(response, self.user_list_url)