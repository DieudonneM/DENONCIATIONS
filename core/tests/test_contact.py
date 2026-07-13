from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.conf import settings


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ContactEmailTest(TestCase):
    def test_contact_form_sends_email_with_reply_to(self):
        url = reverse('core:contact')
        data = {
            'name': 'Jean Dupont',
            'email': 'visitor@example.com',
            'subject': 'Question test',
            'type': 'information',
            'message': 'Bonjour, ceci est un test.'
        }

        response = self.client.post(url, data)

        # Vue redirige après envoi, accepter 302 ou 200 selon implémentation
        self.assertIn(response.status_code, (200, 302))

        # Un email doit être envoyé via le backend locmem
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]

        # Vérifications basiques
        self.assertIn(data['subject'], sent.subject)
        self.assertEqual(sent.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(sent.to, [settings.EMAIL_HOST_USER])

        # Le reply_to doit contenir l'email du visiteur
        self.assertEqual(getattr(sent, 'reply_to', []), [data['email']])

        # Le corps doit contenir le nom et le message du visiteur
        self.assertIn(data['message'], sent.body)
        self.assertIn(data['name'], sent.body)
