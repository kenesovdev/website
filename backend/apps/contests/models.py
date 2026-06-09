from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


DIFFICULTY_XP = {
    'easy': 50,
    'medium': 150,
    'hard': 300,
    'expert': 500,
}


class Contest(models.Model):
    CONTEST_TYPES = [
        ('ICPC', 'ICPC'),
        ('IOI', 'IOI'),
        ('CF', 'Codeforces'),
    ]
    PARTICIPATION_TYPES = [
        ('OPEN', 'Open'),
        ('INVITE_ONLY', 'Invite only'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    contest_type = models.CharField(max_length=10, choices=CONTEST_TYPES, default='CF')
    participation_type = models.CharField(
        max_length=15,
        choices=PARTICIPATION_TYPES,
        default='OPEN',
    )
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
    def display_status(self) -> str:
        mapping = {
            'upcoming': 'UPCOMING',
            'active': 'ONGOING',
            'frozen': 'ONGOING',
            'ended': 'FINISHED',
        }
        return mapping.get(self.status, 'UPCOMING')

    @property
    def is_active(self) -> bool:
        return self.status in ('active', 'frozen')

    @property
    def duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or f'contest-{self.pk or "new"}'
            slug = base
            suffix = 1
            while Contest.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{suffix}'
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContestProblem(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='contest_problems')
    problem = models.ForeignKey('problems.Problem', on_delete=models.CASCADE)
    order_label = models.CharField(max_length=3, default='A')
    order = models.PositiveIntegerField(default=0)
    points = models.IntegerField(default=100)
    xp_reward = models.PositiveIntegerField(default=50)

    class Meta:
        unique_together = [('contest', 'problem'), ('contest', 'order_label')]
        ordering = ['order', 'order_label']

    def save(self, *args, **kwargs):
        if self.problem_id and self.xp_reward == 50 and not self.pk:
            difficulty = self.problem.difficulty
            self.xp_reward = DIFFICULTY_XP.get(difficulty, 50)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.contest.title} — {self.order_label}"


class ContestRegistration(models.Model):
    """Contest participant — tracks join time and XP earned."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contest_registrations',
    )
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    total_xp = models.PositiveIntegerField(default=0)
    last_solve_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('user', 'contest')]

    def __str__(self):
        return f"{self.user.username} @ {self.contest.title}"


class ContestInvite(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
    ]

    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='invites')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contest_invites',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('contest', 'user')]

    def __str__(self):
        return f"Invite {self.user.username} → {self.contest.title} ({self.status})"


class ContestProblemSolve(models.Model):
    """Tracks first AC per user/problem/contest to prevent duplicate XP."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE)
    problem = models.ForeignKey('problems.Problem', on_delete=models.CASCADE)
    submission = models.ForeignKey('submissions.Submission', on_delete=models.CASCADE)
    xp_awarded = models.PositiveIntegerField()
    solved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'contest', 'problem')]

    def __str__(self):
        return f"{self.user.username} solved {self.problem.slug} in {self.contest.title}"


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
