from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import ContestProblem, ContestProblemSolve, ContestRegistration


def award_contest_xp(submission) -> bool:
    """
    Award XP when a submission is AC inside an active contest.
    Returns True if XP was awarded.
    """
    if submission.verdict != 'AC' or submission.status != 'done' or not submission.contest_id:
        return False

    contest = submission.contest
    if not contest.is_active:
        return False

    if ContestProblemSolve.objects.filter(
        user=submission.user,
        contest=contest,
        problem=submission.problem,
    ).exists():
        return False

    try:
        contest_problem = ContestProblem.objects.get(
            contest=contest,
            problem=submission.problem,
        )
    except ContestProblem.DoesNotExist:
        return False

    xp = contest_problem.xp_reward
    now = timezone.now()

    with transaction.atomic():
        ContestProblemSolve.objects.create(
            user=submission.user,
            contest=contest,
            problem=submission.problem,
            submission=submission,
            xp_awarded=xp,
        )
        ContestRegistration.objects.filter(
            user=submission.user,
            contest=contest,
        ).update(
            total_xp=F('total_xp') + xp,
            last_solve_at=now,
        )

    try:
        from .tasks import recalculate_scoreboard
        recalculate_scoreboard.delay(contest.id)
    except Exception:
        pass

    return True
