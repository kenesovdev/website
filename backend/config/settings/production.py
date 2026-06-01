from .base import *  # noqa: F401, F403


def csv_setting(name):
    return [value for value in config(name, default='', cast=Csv()) if value]  # noqa: F405


DEBUG = False
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)  # noqa: F405
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True

CORS_ALLOWED_ORIGINS = csv_setting('CORS_ALLOWED_ORIGINS')
CSRF_TRUSTED_ORIGINS = csv_setting('CSRF_TRUSTED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True
