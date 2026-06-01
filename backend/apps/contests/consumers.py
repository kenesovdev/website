import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ContestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.contest_id = self.scope['url_route']['kwargs']['contest_id']
        self.group_name = f'contest_{self.contest_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            msg = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if msg.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def contest_event(self, event):
        await self.send(text_data=json.dumps(event['data']))
