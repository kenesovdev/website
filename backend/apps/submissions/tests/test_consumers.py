import json
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from channels.routing import URLRouter
from apps.submissions.routing import websocket_urlpatterns
from apps.submissions.models import Submission
from apps.problems.models import Problem

User = get_user_model()


class TestUserMiddleware:
    def __init__(self, inner, user):
        self.inner = inner
        self.user = user

    async def __call__(self, scope, receive, send):
        scope['user'] = self.user
        return await self.inner(scope, receive, send)


class SubmissionConsumerTestCase(TransactionTestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com", handle="owner", password="password"
        )
        self.other = User.objects.create_user(
            email="other@example.com", handle="other", password="password"
        )
        self.problem = Problem.objects.create(
            title="Test Problem", statement="Test statement"
        )
        self.submission = Submission.objects.create(
            user=self.owner,
            problem=self.problem,
            code="print(42)",
            language="python",
            status="pending"
        )
        Submission.objects.filter(id=self.submission.id).update(status='pending', verdict='')
        self.submission.refresh_from_db()

    async def test_owner_can_connect_and_receive_updates(self):
        application = TestUserMiddleware(URLRouter(websocket_urlpatterns), self.owner)
        
        communicator = WebsocketCommunicator(
            application, f"/ws/submissions/{self.submission.id}/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Receive the initial catch-up status update
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "verdict")
        self.assertEqual(response["submission_id"], self.submission.id)
        self.assertEqual(response["status"], "pending")
        self.assertEqual(response["verdict"], "")

        # Simulate group send verdict update (from Celery/channel layer)
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"submission_{self.submission.id}",
            {
                "type": "submission.update",
                "submission_id": self.submission.id,
                "status": "done",
                "verdict": "AC",
                "time_ms": 150,
                "memory_kb": 1024,
            }
        )

        # Receive verdict update from consumer
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "verdict")
        self.assertEqual(response["submission_id"], self.submission.id)
        self.assertEqual(response["status"], "done")
        self.assertEqual(response["verdict"], "AC")
        self.assertEqual(response["time_ms"], 150)
        self.assertEqual(response["memory_kb"], 1024)

        await communicator.disconnect()

    async def test_other_user_connection_closed(self):
        application = TestUserMiddleware(URLRouter(websocket_urlpatterns), self.other)
        
        communicator = WebsocketCommunicator(
            application, f"/ws/submissions/{self.submission.id}/"
        )
        
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)

    async def test_heartbeat_ping_pong(self):
        application = TestUserMiddleware(URLRouter(websocket_urlpatterns), self.owner)
        
        communicator = WebsocketCommunicator(
            application, f"/ws/submissions/{self.submission.id}/"
        )
        
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Drain the initial catch-up status update
        await communicator.receive_json_from()

        # Send a ping
        await communicator.send_json_to({"type": "ping"})

        # Receive pong
        response = await communicator.receive_json_from()
        self.assertEqual(response, {"type": "pong"})

        await communicator.disconnect()
