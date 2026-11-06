"""
Django settings for Peripatos.

Variables de entorno: ver .env.example
DJANGO_ENV=local|production controla ajustes de seguridad y estáticos.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DJANGO_ENV = os.environ.get("DJANGO_ENV", "local")
IS_PROD = DJANGO_ENV == "production"

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-change-me-in-production",
)

DEBUG = os.environ.get("DEBUG", "0") == "1" and not IS_PROD

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "ALLOWED_HOSTS", "localhost,127.0.0.1,backend"
    ).split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]
if not IS_PROD:
    # Frontal de Vite: el navegador envía este origen y su proxy cambia el Host
    CSRF_TRUSTED_ORIGINS += ["http://localhost:5174", "http://127.0.0.1:5174"]


# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "crispy_forms",
    "crispy_bootstrap5",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "import_export",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django_celery_beat",
    "django_celery_results",
    "django_prometheus",
    "peripatos_commands",
    "theory",
    "quizzes",
    "labs",
    "roadmap",
    "dashboard",
    "assistant",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "peripatos.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "peripatos.wsgi.application"


# Database — varias conexiones concurrentes (usuarios simultáneos)
DATABASES = {
    "default": {
        "ENGINE": "django_prometheus.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "peripatos"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "es-es"
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
MAIN_USER_PASS = os.getenv("MAIN_USER_PASS", "")
ADMIN_GROUPS = [g for g in os.getenv("ADMIN_GROUPS", "").split(",") if g]
ROLE_PERMISSIONS = {
    "admin": [],
    "student": [],
}

CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"login": "10/min", "assistant": "20/min"},
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True


# Redis: caché compartida entre workers (sesiones multi-usuario)
_redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
_cache_url = _redis_url.rsplit("/", 1)[0] + "/1"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": _cache_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "peripatos",
    }
}

# Sesiones: cache + DB → varios usuarios simultáneos; sobrevive reinicios de Redis
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = int(os.environ.get("SESSION_COOKIE_AGE", str(60 * 60 * 24 * 14)))
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Asistente. Sin API key, los modelos de Claude no se ofrecen
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    # Tokens del frontal (/static/nt/tokens.css): el admin usa la misma paleta
    ("nt", BASE_DIR / "frontend" / "src" / "styles"),
]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_ROOT = BASE_DIR / "private"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "private": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": PRIVATE_ROOT, "base_url": "/private/"},
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if IS_PROD
        else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Admin (Jazzmin). Los colores salen de static/peripatos-admin/admin.css con los tokens del frontal
JAZZMIN_SETTINGS = {
    "site_title": "Peripatos",
    "site_header": "Peripatos",
    "site_brand": "Peripatos",
    "site_icon": "logo/peripatos.svg",
    "site_logo": "logo/peripatos.svg",
    "login_logo": "logo/peripatos.svg",
    "welcome_sign": "Inicia sesión en la administración",
    "copyright": "Peripatos",
    "use_google_fonts_cdn": False,  # las fuentes del frontal se cargan en templates/admin
    "show_ui_builder": False,
    # Font Awesome 6 Free (el que trae Jazzmin)
    "icons": {
        "auth.group": "fas fa-users",
        "auth.user": "fas fa-user",
        "authtoken.tokenproxy": "fas fa-key",
        "django_celery_results.groupresult": "fas fa-layer-group",
        "django_celery_results.taskresult": "fas fa-clipboard-check",
        "django_celery_beat.periodictask": "fas fa-arrows-rotate",
        "django_celery_beat.clockedschedule": "fas fa-clock",
        "django_celery_beat.crontabschedule": "fas fa-calendar-days",
        "django_celery_beat.intervalschedule": "fas fa-stopwatch",
        "django_celery_beat.solarschedule": "fas fa-sun",
        "theory.material": "fas fa-book-open",
        "quizzes.topic": "fas fa-tags",
        "quizzes.quiz": "fas fa-clipboard-question",
        "quizzes.question": "fas fa-circle-question",
        "quizzes.attempt": "fas fa-list-check",
        "labs.lab": "fas fa-flask",
        "labs.submission": "fas fa-file-arrow-up",
        "roadmap.training": "fas fa-route",
        "roadmap.careerpath": "fas fa-signs-post",
        "roadmap.pathstage": "fas fa-layer-group",
        "dashboard.notice": "fas fa-bell",
        "assistant.llmmodel": "fas fa-microchip",
    },
}
JAZZMIN_UI_TWEAKS = {
    "theme": "default",
    "default_theme_mode": "light",  # el modo real lo decide el tema elegido (nt-theme)
    "navbar": "",
    "sidebar": "",
    "brand_colour": "",
    "accent": "",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-secondary",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-primary",  # «Guardar» y «Añadir» son la acción principal de cada vista
    },
}

# Seguridad en producción (detrás de nginx / WAF)
if IS_PROD:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1") == "1"
    CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "1") == "1"
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "0") == "1"
