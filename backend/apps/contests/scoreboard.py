from django.db.models import F

from .models import ContestRegistration


def calculate_scoreboard(contest, up_to_time=None):
    """
    XP standings: total_xp DESC, then last_solve_at ASC (earlier is better).
    """
    registrations = (
        ContestRegistration.objects
        .filter(contest=contest)
        .select_related('user')
        .order_by(
            F('total_xp').desc(nulls_last=True),
            F('last_solve_at').asc(nulls_last=True),
            'registered_at',
        )
    )

    rows = []
    rank = 1
    for reg in registrations:
        rows.append({
            'rank': rank,
            'user_id': str(reg.user_id),
            'handle': reg.user.handle,
            'total_xp': reg.total_xp,
            'last_solve_at': reg.last_solve_at.isoformat() if reg.last_solve_at else None,
            'joined_at': reg.registered_at.isoformat(),
        })
        rank += 1

    return {
        'contest_id': contest.id,
        'title': contest.title,
        'rows': rows,
    }
