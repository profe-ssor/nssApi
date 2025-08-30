from datetime import timedelta

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / '.env'
print(f"Looking for .env at: {dotenv_path.absolute()}")
load_dotenv(dotenv_path)

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,nssapi.onrender.com").split(",")

# Frontend URL for email verification links
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://nss-dems.vercel.app")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'digital360Api',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'nss_personnel',
    'nss_supervisors',
    'nss_admin',
    'file_uploads',
    'messageApp',
    'evaluations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
       'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'TOKEN_TYPE_IN': 'access',
    'REFRESH_TOKEN_LIFETIME': timedelta(days=2),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_TOKEN_PREFIX': 'blacklisted-',
}

AUTH_USER_MODEL = 'digital360Api.MyUser'
ROOT_URLCONF = 'nssApi.urls'

# CORS Configuration - Fixed for production
CORS_ALLOWED_ORIGINS = [
    "https://nss-dems.vercel.app",  # Fixed: removed /login path
    "https://nssapi.onrender.com"
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# Allow all subdomains of vercel.app for preview deployments (optional)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://nss-dems-.*\.vercel\.app$",  # This allows preview deployments
]

CORS_ALLOW_CREDENTIALS = True

# Additional CORS settings for better compatibility
CORS_ALLOW_ALL_ORIGINS = False  # Keep this False for security
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://nss-dems.vercel.app",  # Fixed: removed /login path
    "https://nssapi.onrender.com",
]

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'nssApi.wsgi.application'

# Database Configuration
DATABASES = {
    'default': dj_database_url.parse(os.environ.get("DATABASE_URL"))
}

# Static files configuration
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv('EMAIL_HOST')  # smtp.gmail.com
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 465))  # 465
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # Your full email
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # App password
EMAIL_USE_TLS = False  # Must be False when using SSL
EMAIL_USE_SSL = True  # True for port 465
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')