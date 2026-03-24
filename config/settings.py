# config/settings.py
"""
Django settings for config project.

Adaptado para deploy en Render (gunicorn + WhiteNoise).
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY: en producción pon SECRET_KEY como variable de entorno en Render
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-#3kp(nqgy-_)%so%*d4+sle2$%^0akdqghqz=6ff6-f0faz(82",
)

# DEBUG controlado por variable de entorno
DEBUG = os.environ.get("DEBUG", "False") == "True"

# ALLOWED_HOSTS desde variable, por defecto el dominio de Render de tu app.
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "diabetes-app-eby0.onrender.com,127.0.0.1,localhost,[::1]",
).split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "diabetes_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise debe ir lo más arriba posible después de SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # añade rutas si usas plantillas fuera de las apps
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database (sqlite por ahora)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Email settings (controlados por variables de entorno)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587") or 587)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_USE_TLS = (
    os.getenv("EMAIL_USE_TLS", "true").lower() == "true" and not EMAIL_USE_SSL
)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@diabetes.local")

# Fallback seguro para despliegues iniciales: consola o SMTP según variables.
# En Render: para evitar ImproperlyConfigured cuando DEBUG=False usa ALLOW_CONSOLE_EMAIL=True temporalmente.
ALLOW_CONSOLE_EMAIL = os.environ.get("ALLOW_CONSOLE_EMAIL", "True") == "True"

if DEBUG or ALLOW_CONSOLE_EMAIL:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    if EMAIL_HOST:
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    else:
        raise ImproperlyConfigured(
            "Configura SMTP en variables de entorno: EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD."
        )


# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Añadimos explícitamente la carpeta static de la app (además de una posible carpeta static/ en la raíz)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "diabetes_app", "static"),
]

# Storage de WhiteNoise. Usamos Manifest por defecto (hashing) pero permitimos desactivarlo para debugging.
if os.environ.get("DISABLE_MANIFEST_STATIC", "False") == "True":
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# Seguridad adicional
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if os.environ.get("CSRF_TRUSTED_ORIGINS") else []

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
