"""
WSGI config for denunciations_app project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'denunciations_app.settings')

application = get_wsgi_application()
