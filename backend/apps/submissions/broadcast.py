from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def submission_status_payload(sub) -> dict:
    return {
        'type': 'status_update',
        'submission_id': sub.id,
        'status': sub.status,
        'verdict': sub.verdict,
        'time_ms': sub.time_ms,
        'memory_kb': sub.memory_kb,
    }


def broadcast_submission_status(sub) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f'submission_{sub.id}',
        {
            'type': 'submission.update',
            'data': submission_status_payload(sub),
        },
    )
