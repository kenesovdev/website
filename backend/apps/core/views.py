from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health(request):
    db_ok = redis_ok = False
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        pass
    try:
        cache.set('_hc', '1', 5)
        redis_ok = cache.get('_hc') == '1'
    except Exception:
        pass
    code = 200 if (db_ok and redis_ok) else 503
    return JsonResponse({
        'status': 'ok' if code == 200 else 'degraded',
        'database': 'ok' if db_ok else 'error',
        'redis': 'ok' if redis_ok else 'error',
        'version': '0.1.0',
    }, status=code)
