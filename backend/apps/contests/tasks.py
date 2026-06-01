from datetime import timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.utils import timezone

from .models import Contest, ScoreboardSnapshot


logger = get_task_logger(__name__)


def _ws_event(contest_id, payload):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.debug('No channel layer configured; skipped contest event %s', payload)
        return

    async_to_sync(channel_layer.group_send)(
        f'contest_{contest_id}',
        {'type': 'contest.event', 'data': payload}
    )


def _store_snapshot(contest, data, snapshot_type):
    snapshot = (
        ScoreboardSnapshot.objects
        .filter(contest=contest, snapshot_type=snapshot_type)
        .order_by('-taken_at')
        .first()
    )
    if snapshot:
        snapshot.data = data
        snapshot.save(update_fields=['data'])
        return snapshot

    return ScoreboardSnapshot.objects.create(
        contest=contest,
        data=data,
        snapshot_type=snapshot_type,
    )


@shared_task(name='apps.contests.tasks.check_contest_transitions')
def check_contest_transitions():
    now = timezone.now()
    relevant = Contest.objects.filter(
        start_time__lte=now + timedelta(hours=6),
        end_time__gte=now - timedelta(days=1),
    )
    for contest in relevant:
        prev = cache.get(f'contest_prev_status_{contest.id}', 'unknown')
        curr = contest.status
        if prev != curr:
            if curr == 'active':
                _ws_event(contest.id, {'type': 'contest_started'})
            elif curr == 'frozen':
                freeze_scoreboard.delay(contest.id)
                _ws_event(contest.id, {'type': 'scoreboard_frozen'})
            elif curr == 'ended':
                finalize_contest.delay(contest.id)
            cache.set(f'contest_prev_status_{contest.id}', curr, timeout=86400)


@shared_task(name='apps.contests.tasks.notify_5min_before_end')
def notify_5min_before_end():
    now = timezone.now()
    ending_soon = Contest.objects.filter(
        end_time__gte=now + timedelta(minutes=4, seconds=30),
        end_time__lte=now + timedelta(minutes=5, seconds=30)
    )
    for contest in ending_soon:
        key = f'notif_5min_sent_{contest.id}'
        if not cache.get(key):
            _ws_event(contest.id, {
                'type': 'contest_ending_soon',
                'minutes_left': 5,
                'end_time': contest.end_time.isoformat()
            })
            cache.set(key, True, timeout=600)


@shared_task(name='apps.contests.tasks.freeze_scoreboard')
def freeze_scoreboard(contest_id):
    from .scoreboard import calculate_scoreboard

    try:
        contest = Contest.objects.get(id=contest_id)
    except Contest.DoesNotExist:
        logger.warning('Contest %s not found for freeze snapshot', contest_id)
        return None

    data = calculate_scoreboard(contest, up_to_time=contest.freeze_time)
    _store_snapshot(contest, data, 'freeze')
    return data


@shared_task(name='apps.contests.tasks.finalize_contest')
def finalize_contest(contest_id):
    from .scoreboard import calculate_scoreboard

    try:
        contest = Contest.objects.get(id=contest_id)
    except Contest.DoesNotExist:
        logger.warning('Contest %s not found for final snapshot', contest_id)
        return None

    data = calculate_scoreboard(contest, up_to_time=contest.end_time)
    _store_snapshot(contest, data, 'final')
    _ws_event(contest_id, {'type': 'contest_ended', 'final_scoreboard': data})
    return data


@shared_task(name='apps.contests.tasks.recalculate_scoreboard')
def recalculate_scoreboard(contest_id):
    from .scoreboard import calculate_scoreboard

    try:
        contest = Contest.objects.get(id=contest_id)
    except Contest.DoesNotExist:
        logger.warning('Contest %s not found for live scoreboard recalculation', contest_id)
        return None

    data = calculate_scoreboard(contest)
    cache.set(f'scoreboard_live_{contest_id}', data, timeout=30)
    if contest.status != 'frozen':
        _ws_event(contest_id, {'type': 'scoreboard_update', 'data': data})
    return data
