import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()


def websocket_urlpatterns():
    from apps.contests.routing import websocket_urlpatterns as contest_patterns
    from apps.submissions.routing import websocket_urlpatterns as submission_patterns

    return submission_patterns + contest_patterns


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns())
    ),
})
