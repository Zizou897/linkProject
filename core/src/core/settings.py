from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='vozavi.online,www.vozavi.online').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in config('CSRF_TRUSTED_ORIGINS', default='').split(',') if o.strip()]

# Identifiant de mesure Google Analytics 4. Actif en production (default), désactivé
# en développement (DEBUG) pour ne pas polluer les statistiques avec le trafic local.
# Surchargeable via le .env (GA_MEASUREMENT_ID). Exposé aux templates via
# app.context_processors ; le suivi ne se charge qu'après consentement (bandeau cookies).
GA_MEASUREMENT_ID = config('GA_MEASUREMENT_ID', default='' if DEBUG else 'G-EV5EW8J48F')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'django_celery_results',
    'after_response',
]

LOCAL_APPS = [
    'app',
    'backoffice',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ── Base de données ───────────────────────────────────────────────────

if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME':     config('DB_NAME', default='vozavi_bd'),
            'USER':     config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST':     config('DB_HOST', default='localhost'),
            'PORT':     config('DB_PORT', default='3306'),
            'CONN_MAX_AGE': 60,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'static_cdn'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Le test runner force DEBUG=False, ce qui active le manifeste statique
# (CompressedManifestStaticFilesStorage) — celui-ci exige un collectstatic
# préalable et fait échouer {% static %} dans les templates. En contexte de test,
# on bascule sur un stockage statique sans manifeste.
import sys
if 'test' in sys.argv:
    STORAGES['staticfiles']['BACKEND'] = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media_cdn'

# Documents envoyés par les répondants (questions de type 'file').
# Hors de MEDIA_ROOT : /media/ est servi publiquement, ces documents ne doivent
# être accessibles que via la vue protégée (créateur du formulaire connecté).
PRIVATE_MEDIA_ROOT = BASE_DIR / 'private_media'
if 'test' in sys.argv:
    # Les uploads de test vont dans un dossier temporaire jetable, pas dans
    # private_media/ (sinon chaque run de tests y laisse des fichiers).
    import tempfile
    PRIVATE_MEDIA_ROOT = Path(tempfile.mkdtemp(prefix='vozavi_test_private_'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/connexion/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ── Cache (Django DB) ─────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'vozavi_cache',
        'TIMEOUT': 300,
    }
}

# ── Celery (broker SQLAlchemy + backend Django DB) ────────────────────
# Broker : SQLite en dev, MySQL en prod (même DB que Django)
if DEBUG:
    CELERY_BROKER_URL = config(
        'CELERY_BROKER_URL',
        default=f'sqla+sqlite:///{BASE_DIR}/celery_broker.sqlite3',
    )
else:
    _db_user = config('DB_USER', default='root')
    _db_pass = config('DB_PASSWORD', default='')
    _db_host = config('DB_HOST', default='localhost')
    _db_port = config('DB_PORT', default='3306')
    _db_name = config('DB_NAME', default='vozavi_bd')
    CELERY_BROKER_URL = config(
        'CELERY_BROKER_URL',
        default=f'sqla+mysql+pymysql://{_db_user}:{_db_pass}@{_db_host}:{_db_port}/{_db_name}',
    )

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 5 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 4 * 60
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ── Email (Gmail via SMTP) ────────────────────────────────────────────
# Gmail : host=smtp.gmail.com, user = adresse complète, password = mot de
# passe d'application (myaccount.google.com/apppasswords, 16 caractères).
# EMAIL_TIMEOUT évite qu'un SMTP injoignable bloque le thread d'envoi.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='contact.vozavi@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL',
                            default='Vozavi <contact.vozavi@gmail.com>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL


if not DEBUG:
    # Derrière nginx (proxy TLS) : Gunicorn parle HTTP, nginx ajoute
    # X-Forwarded-Proto. Sans ceci, SECURE_SSL_REDIRECT crée une boucle.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # HSTS : force HTTPS côté navigateur. 1 an + sous-domaines (le site redirige déjà en SSL).
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ── Limites d'upload (anti-DoS / anti-saturation disque) ──────────────
# Plafonne la taille des requêtes et des fichiers (logos de formulaire).
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 Mo (champs non-fichier)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 Mo en mémoire avant temp file
