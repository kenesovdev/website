from django.urls import path
from .consumers import ContestConsumer

websocket_urlpatterns = [
    path('ws/contest/<int:contest_id>/', ContestConsumer.as_asgi()),
]
