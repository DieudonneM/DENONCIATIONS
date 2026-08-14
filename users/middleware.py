from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from users.services import TEMPORARY_PASSWORD_TTL


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and getattr(user, 'must_change_password', False):
            set_at = getattr(user, 'temp_password_set_at', None)
            if set_at is None or timezone.now() - set_at > TEMPORARY_PASSWORD_TTL:
                logout(request)
                messages.error(
                    request,
                    'Le mot de passe temporaire a expiré. Demandez une nouvelle réinitialisation.',
                )
                return redirect('users:login')

            allowed_paths = {
                reverse('users:password_change'),
                reverse('users:logout'),
            }
            if request.path not in allowed_paths:
                if request.path.startswith('/api/'):
                    return JsonResponse(
                        {'detail': 'Vous devez personnaliser votre mot de passe.'},
                        status=403,
                    )
                return redirect('users:password_change')

        return self.get_response(request)