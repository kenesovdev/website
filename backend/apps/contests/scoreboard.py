def calculate_scoreboard(contest, up_to_time=None):
    """
    Stub for scoreboard calculation.

    up_to_time is accepted so lifecycle tasks can calculate frozen/final
    snapshots against a stable cutoff while the real scoring logic evolves.
    """
    return {
        "contest_id": contest.id,
        "title": contest.title,
        "rows": []
    }
