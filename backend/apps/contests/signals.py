from django.db.models.signals import post_save
from django.dispatch import receiver


def register():
    from apps.submissions.models import Submission

    @receiver(post_save, sender=Submission)
    def on_submission_done(sender, instance, **kwargs):
        if instance.status == 'done' and instance.verdict == 'AC':
            from .xp import award_contest_xp
            award_contest_xp(instance)
