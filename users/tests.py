from django.contrib.auth import authenticate
from django.test import Client, TestCase
from django.urls import reverse

from users.models import User


class TemporaryPasswordFlowTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username='admin',
			email='admin@example.com',
			password='AdminPassword2026!',
			role='administrateur',
		)
		self.user = User.objects.create_user(
			username='worker',
			email='worker@example.com',
			password='OldPassword2026!',
			role='travailleur',
		)

	def _reset_password_as_admin(self):
		self.client.force_login(
			self.admin,
			backend='users.auth_backends.EmailBackend',
		)
		edit_url = reverse('core:admin_users_edit', args=[self.user.pk])
		response = self.client.post(
			edit_url,
			{'action': 'reset_password'},
		)
		self.assertRedirects(
			response,
			edit_url,
			fetch_redirect_response=False,
		)
		return edit_url, self.client.session['admin_temporary_password']['password']

	def test_admin_reset_displays_secret_once_and_invalidates_old_password(self):
		edit_url, temporary_password = self._reset_password_as_admin()

		self.user.refresh_from_db()
		self.assertTrue(self.user.must_change_password)
		self.assertIsNotNone(self.user.temp_password_set_at)
		self.assertIsNone(self.user.temp_password_used_at)
		self.assertFalse(self.user.check_password('OldPassword2026!'))

		first_display = self.client.get(edit_url)
		self.assertContains(first_display, temporary_password)
		second_display = self.client.get(edit_url)
		self.assertNotContains(second_display, temporary_password)

	def test_temporary_password_authenticates_once_then_forces_change(self):
		_, temporary_password = self._reset_password_as_admin()
		user_client = Client()

		login_response = user_client.post(
			reverse('users:login'),
			{'username': self.user.email, 'password': temporary_password},
		)
		self.assertRedirects(
			login_response,
			reverse('users:password_change'),
			fetch_redirect_response=False,
		)

		self.user.refresh_from_db()
		self.assertIsNotNone(self.user.temp_password_used_at)
		blocked_page = user_client.get(reverse('core:dashboard'))
		self.assertRedirects(
			blocked_page,
			reverse('users:password_change'),
			fetch_redirect_response=False,
		)

		second_client = Client()
		second_login = second_client.post(
			reverse('users:login'),
			{'username': self.user.email, 'password': temporary_password},
		)
		self.assertEqual(second_login.status_code, 200)
		self.assertNotIn('_auth_user_id', second_client.session)

		unchanged_response = user_client.post(
			reverse('users:password_change'),
			{
				'old_password': temporary_password,
				'new_password1': temporary_password,
				'new_password2': temporary_password,
			},
		)
		self.assertEqual(unchanged_response.status_code, 200)
		self.assertContains(
			unchanged_response,
			'doit être différent du mot de passe temporaire',
		)

		new_password = 'NouveauMotDePasse2026!'
		change_response = user_client.post(
			reverse('users:password_change'),
			{
				'old_password': temporary_password,
				'new_password1': new_password,
				'new_password2': new_password,
			},
		)
		self.assertRedirects(
			change_response,
			reverse('users:password_change_done'),
			fetch_redirect_response=False,
		)

		self.user.refresh_from_db()
		self.assertFalse(self.user.must_change_password)
		self.assertIsNone(self.user.temp_password_set_at)
		self.assertIsNone(self.user.temp_password_used_at)
		self.assertIsNotNone(
			authenticate(username=self.user.email, password=new_password),
		)

	def test_admin_cannot_reset_own_password(self):
		self.client.force_login(
			self.admin,
			backend='users.auth_backends.EmailBackend',
		)
		edit_url = reverse('core:admin_users_edit', args=[self.admin.pk])
		self.client.post(edit_url, {'action': 'reset_password'})

		self.admin.refresh_from_db()
		self.assertFalse(self.admin.must_change_password)
		self.assertTrue(self.admin.check_password('AdminPassword2026!'))

	def test_mobile_login_refuses_temporary_password_without_consuming_it(self):
		_, temporary_password = self._reset_password_as_admin()
		mobile_client = Client()

		response = mobile_client.post(
			reverse('api:api_login'),
			data={
				'email': self.user.email,
				'password': temporary_password,
			},
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 403)
		self.assertTrue(response.json()['password_change_required'])
		self.user.refresh_from_db()
		self.assertIsNone(self.user.temp_password_used_at)
