import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Submission


class SubmissionConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.submission_id = self.scope['url_route']['kwargs']['submission_id']
        self.group_name = f"submission_{self.submission_id}"

        # Only allow the submission owner OR staff to connect
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        allowed = await self.is_allowed(user, self.submission_id)
        if not allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current status immediately on connect (catch-up)
        status_data = await self.get_current_status(self.submission_id)
        await self.send(text_data=json.dumps(status_data))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        # Handle heartbeat ping from frontend
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except (json.JSONDecodeError, KeyError):
            pass

    async def submission_update(self, event):
        # Called by channel layer when Celery publishes a verdict
        await self.send(text_data=json.dumps({
            "type": "verdict",
            "submission_id": event["submission_id"],
            "status": event["status"],
            "verdict": event.get("verdict", ""),
            "time_ms": event.get("time_ms"),
            "memory_kb": event.get("memory_kb"),
        }))

    @database_sync_to_async
    def is_allowed(self, user, submission_id):
        try:
            sub = Submission.objects.get(pk=submission_id)
            return sub.user == user or user.is_staff
        except Submission.DoesNotExist:
            return False

    @database_sync_to_async
    def get_current_status(self, submission_id):
        try:
            sub = Submission.objects.get(pk=submission_id)
            return {
                "type": "verdict",
                "submission_id": sub.id,
                "status": sub.status,
                "verdict": sub.verdict or "",
                "time_ms": sub.time_ms,
                "memory_kb": sub.memory_kb,
            }
        except Submission.DoesNotExist:
            return {"type": "error", "message": "Submission not found"}
