"""
WSGI config for nssApi project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nssApi.settings')

application = get_wsgi_application()

# Configure WhiteNoise for static files
application = WhiteNoise(application, root=settings.STATIC_ROOT, prefix=settings.STATIC_URL)

# In production, also serve media files through WhiteNoise
if not settings.DEBUG:
    # Ensure media directories exist
    media_dirs = [
        os.path.join(settings.MEDIA_ROOT, 'documents'),
        os.path.join(settings.MEDIA_ROOT, 'signed_docs'),
        os.path.join(settings.MEDIA_ROOT, 'signatures')
    ]
    
    for media_dir in media_dirs:
        if not os.path.exists(media_dir):
            os.makedirs(media_dir, exist_ok=True)
    
    # Add media files to WhiteNoise
    application.add_files(settings.MEDIA_ROOT, prefix='media/')
