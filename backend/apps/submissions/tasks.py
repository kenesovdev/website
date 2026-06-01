import os
import subprocess
import tempfile
import time
from datetime import timedelta

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.utils import timezone

logger = get_task_logger(__name__)

LANG_CONFIG = {
    'python': {
        'ext': '.py',
        'compile': None,
        'run': ['python3', '{file}'],
    },
    'cpp': {
        'ext': '.cpp',
        'compile': ['g++', '-O2', '-std=c++17', '-o', '{exe}', '{file}'],
        'run': ['{exe}'],
    },
    'java': {
        'ext': '.java',
        'compile': ['javac', '{file}'],
        'run': ['java', '-cp', '{dir}', 'Main'],
    },
}


@shared_task(name='apps.submissions.tasks.cleanup_stuck_submissions', queue='judge')
def cleanup_stuck_submissions(minutes: int = 30) -> int:
    from apps.submissions.models import Submission

    cutoff = timezone.now() - timedelta(minutes=minutes)
    return Submission.objects.filter(
        status__in=['pending', 'judging'],
        created_at__lt=cutoff,
    ).update(status='error', verdict=None)


def _get_test_cases(problem) -> list[dict[str, str]]:
    return [
        {'input': tc.input, 'expected_output': tc.expected_output}
        for tc in problem.test_cases.order_by('order', 'created_at')
    ]


def run_judge(sub) -> tuple[str, int, int]:
    """Run all test cases. Returns (verdict, time_ms, memory_kb)."""
    problem = sub.problem
    lang = sub.language
    cfg = LANG_CONFIG[lang]
    test_cases = _get_test_cases(problem)

    if not test_cases:
        return 'AC', 0, 0

    time_limit_ms = problem.time_ms
    time_limit_s = time_limit_ms / 1000.0

    with tempfile.TemporaryDirectory() as tmpdir:
        if lang == 'java':
            src_path = os.path.join(tmpdir, 'Main' + cfg['ext'])
        else:
            src_path = os.path.join(tmpdir, 'solution' + cfg['ext'])

        with open(src_path, 'w', encoding='utf-8') as handle:
            handle.write(sub.code)

        exe_path = os.path.join(tmpdir, 'solution')

        if cfg['compile']:
            compile_cmd = [
                part.format(file=src_path, exe=exe_path, dir=tmpdir)
                for part in cfg['compile']
            ]
            result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return 'CE', 0, 0

        max_time_ms = 0
        max_memory_kb = 0

        for test_case in test_cases:
            run_cmd = [
                part.format(file=src_path, exe=exe_path, dir=tmpdir)
                for part in cfg['run']
            ]
            start = time.perf_counter()
            try:
                proc = subprocess.run(
                    run_cmd,
                    input=test_case['input'],
                    capture_output=True,
                    text=True,
                    timeout=time_limit_s + 1,
                )
            except subprocess.TimeoutExpired:
                return 'TLE', int(time_limit_s * 1000), max_memory_kb

            elapsed_ms = int((time.perf_counter() - start) * 1000)
            max_time_ms = max(max_time_ms, elapsed_ms)

            if elapsed_ms > time_limit_ms:
                return 'TLE', elapsed_ms, max_memory_kb

            if proc.returncode != 0:
                return 'RE', elapsed_ms, max_memory_kb

            got = proc.stdout.strip()
            expected = test_case['expected_output'].strip()
            if got != expected:
                return 'WA', elapsed_ms, max_memory_kb

        return 'AC', max_time_ms, max_memory_kb


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    queue='judge',
    name='apps.submissions.judge_submission',
    acks_late=True,
    soft_time_limit=120,
    time_limit=180,
)
def judge_submission(self, submission_id: int):
    from apps.submissions.models import FailedSubmission, Submission

    try:
        sub = Submission.objects.select_related('problem').get(id=submission_id)
    except Submission.DoesNotExist:
        logger.error('Submission %s not found', submission_id)
        return

    sub.status = 'judging'
    sub.save(update_fields=['status'])

    # Publish intermediate status JUDGING immediately
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"submission_{sub.id}",
                {
                    "type": "submission.update",
                    "submission_id": sub.id,
                    "status": "JUDGING",
                    "verdict": "",
                    "time_ms": None,
                    "memory_kb": None,
                }
            )
    except Exception as exc:
        logger.error("Failed to publish intermediate status: %s", exc)

    try:
        verdict, time_ms, memory_kb = run_judge(sub)
        sub.verdict = verdict
        sub.status = 'done'
        sub.time_ms = time_ms
        sub.memory_kb = memory_kb
        sub.save(update_fields=['status', 'verdict', 'time_ms', 'memory_kb'])

        # Publish final verdict status
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"submission_{sub.id}",
                    {
                        "type": "submission.update",
                        "submission_id": sub.id,
                        "status": sub.status,
                        "verdict": sub.verdict or "",
                        "time_ms": sub.time_ms,
                        "memory_kb": sub.memory_kb,
                    }
                )
        except Exception as exc_ws:
            logger.error("Failed to publish final status: %s", exc_ws)

        logger.info('[judge] #%s → %s (%sms)', submission_id, verdict, time_ms)
    except Exception as exc:
        logger.warning('Judge error on submission %s: %s', submission_id, exc)
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries * 5) from exc
        except MaxRetriesExceededError:
            sub.status = 'error'
            sub.verdict = None
            sub.save(update_fields=['status', 'verdict', 'time_ms', 'memory_kb'])

            # Publish error status
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                if channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        f"submission_{sub.id}",
                        {
                            "type": "submission.update",
                            "submission_id": sub.id,
                            "status": sub.status,
                            "verdict": "",
                            "time_ms": None,
                            "memory_kb": None,
                        }
                    )
            except Exception as exc_ws:
                logger.error("Failed to publish error status: %s", exc_ws)

            FailedSubmission.objects.update_or_create(
                submission=sub,
                defaults={
                    'error_message': str(exc),
                    'retry_count': self.request.retries,
                },
            )
            logger.error('[judge] #%s dead-lettered after max retries', submission_id)
