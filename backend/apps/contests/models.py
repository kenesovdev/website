from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Contest(models.Model):
    CONTEST_TYPES = [
        ('ICPC', 'ICPC'),
        ('IOI', 'IOI'),
        ('CF', 'Codeforces'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    contest_type = models.CharField(max_length=10, choices=CONTEST_TYPES, default='ICPC')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    freeze_time = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_contests',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def status(self) -> str:
        now = timezone.now()
        if now < self.start_time:
            return 'upcoming'
        if now > self.end_time:
            return 'ended'
        if self.freeze_time and now >= self.freeze_time:
            return 'frozen'
        return 'active'

    @property
    def is_active(self) -> bool:
        return self.status in ('active', 'frozen')

    @property
    def duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='contest_problems')
    problem = models.ForeignKey('problems.Problem', on_delete=models.CASCADE)
    order_label = models.CharField(max_length=3, default='A')
    points = models.IntegerField(default=100)

    class Meta:
        unique_together = [('contest', 'problem'), ('contest', 'order_label')]
        ordering = ['order_label']

    def __str__(self):
        return f"{self.contest.title} — {self.order_label}"


class ContestRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contest_registrations')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'contest')]

    def __str__(self):
        return f"{self.user.username} @ {self.contest.title}"


class ScoreboardSnapshot(models.Model):
    SNAPSHOT_TYPES = [
        ('live', 'Live'),
        ('freeze', 'Freeze'),
        ('final', 'Final'),
    ]

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='snapshots')
    data = models.JSONField()
    snapshot_type = models.CharField(max_length=10, choices=SNAPSHOT_TYPES, default='live')
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at']

    def __str__(self):
        return f"{self.contest.title} — {self.snapshot_type} @ {self.taken_at}"
