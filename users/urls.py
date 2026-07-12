"""
URLs pour l'application users.
"""

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import ForcePasswordChangeView

app_name = 'users'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    # Password change (force after first login)
    path('password/change/', ForcePasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/auth/password_change_done.html'
    ), name='password_change_done'),
]
