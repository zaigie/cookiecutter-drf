import os
from datetime import timedelta

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from utils.cfg import cfg

from .base import BASE_DIR, INSTALLED_APPS

# Apps
INSTALLED_APPS.insert(0, "simpleui")
INSTALLED_APPS += [
    "rest_framework",
    "corsheaders",
    "django_filters",
    "import_export",
]
INSTALLED_APPS += [
    "auth",
]

# System
DEBUG = cfg("debug", is_bool=True)
ALLOWED_HOSTS = ["*"]
AUTH_USER_MODEL = "auth.User"

# Databases
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATABASE_HOST = cfg("database", "host")
DATABASE_PORT = cfg("database", "port")
DATABASE_USER = cfg("database", "user")
DATABASE_PSWD = cfg("database", "pswd")
DATABASES = {
    "default": dj_database_url.config(
        default=f"{{cookiecutter.database}}://{DATABASE_USER}:{DATABASE_PSWD}@{DATABASE_HOST}:{DATABASE_PORT}/{{cookiecutter.project_name}}",
        conn_max_age=600,
    )
}

# Redis
REDIS_HOST = cfg("redis", "host")
REDIS_PORT = cfg("redis", "port")
REDIS_PSWD = cfg("redis", "pswd")

# Rest framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_RENDERER_CLASSES": (
        "custom.renderers.CustomRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "EXCEPTION_HANDLER": "custom.exceptions.custom_exception_handler",
}

# Jwt
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=80),
    "AUTH_HEADER_TYPES": ("Bearer", "JWT"),
    "USER_ID_FIELD": "id",
}

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Caches
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_PSWD}@{REDIS_HOST}:{REDIS_PORT}/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Sentry
SENTRY_DSN = cfg("sentry", "dsn")
if not DEBUG and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )

# Logging
LOG_ROOT = os.path.join(BASE_DIR, "logs")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s][%(levelname)s] %(name)s %(filename)s:%(funcName)s:%(lineno)d %(message)s",
        }
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "warning": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_ROOT, "warning.log"),
            "maxBytes": 1024 * 1024 * 200,
            "backupCount": 10,
            "formatter": "default",
            "encoding": "utf-8",
        },
        "error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_ROOT, "error.log"),
            "maxBytes": 1024 * 1024 * 300,
            "backupCount": 10,
            "formatter": "default",
            "encoding": "utf-8",
        },
    },
    "root": {"handlers": ["console"], "level": "DEBUG"},
    "loggers": {
        "django": {
            "handlers": ["console", "warning", "error"],
            "propagate": True,
        }
    },
}
for handler in LOGGING["handlers"].values():
    if "filename" in handler:
        os.makedirs(os.path.dirname(handler["filename"]), exist_ok=True)

# Cors
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = ()
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
    "VIEW",
)
CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

# Internationalization
LANGUAGE_CODE = "{{cookiecutter.language}}"
TIME_ZONE = "{{cookiecutter.timezone}}"
USE_I18N = True
USE_L10N = True
USE_TZ = False
