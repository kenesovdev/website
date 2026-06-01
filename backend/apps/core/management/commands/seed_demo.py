import os
import secrets
import string
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contests.models import Contest, ContestProblem, ContestRegistration
from apps.problems.models import Problem, Tag, TestCase
from apps.submissions.models import Submission


class Command(BaseCommand):
    help = 'Create a demo admin, problem, contests, participants, and submissions.'

    def add_arguments(self, parser):
        parser.add_argument('--admin-email', default=os.environ.get('ADMIN_EMAIL', 'codeadmin@codearena.local'))
        parser.add_argument('--admin-handle', default=os.environ.get('ADMIN_HANDLE', 'codeadmin'))
        parser.add_argument('--admin-password', default=os.environ.get('ADMIN_PASSWORD'))
        parser.add_argument('--participant-password', default=os.environ.get('PARTICIPANT_PASSWORD', 'DemoPass2026!'))

    def handle(self, *args, **options):
        User = get_user_model()
        admin_password = options['admin_password'] or self._generate_password()
        admin, created_admin = User.objects.get_or_create(
            email=options['admin_email'],
            defaults={
                'handle': options['admin_handle'],
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_verified': True,
            },
        )
        admin.handle = options['admin_handle']
        admin.role = 'admin'
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.is_verified = True
        if created_admin or options['admin_password']:
            admin.set_password(admin_password)
        admin.save()

        problem = self._seed_problem(admin)
        contests = self._seed_contests(admin, problem)
        participants = self._seed_participants(User, options['participant_password'])
        self._seed_registrations(contests, participants)
        self._seed_submissions(contests[0], problem, participants)

        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
        self.stdout.write(f'Admin email: {admin.email}')
        if created_admin or options['admin_password']:
            self.stdout.write(f'Admin password: {admin_password}')
        else:
            self.stdout.write('Admin password was not changed because the admin already existed.')
        self.stdout.write(f'Participant password: {options["participant_password"]}')

    def _generate_password(self) -> str:
        alphabet = string.ascii_letters + string.digits + '-_!@#$%'
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(24))
            if (
                any(char.islower() for char in password)
                and any(char.isupper() for char in password)
                and any(char.isdigit() for char in password)
                and any(char in '-_!@#$%' for char in password)
            ):
                return password

    def _seed_problem(self, admin):
        statement = '''# Sum of Two Numbers

Given two integers `a` and `b`, print their sum.

## Input
Two integers `a` and `b` separated by a space.

## Output
Print one integer: `a + b`.

## Example
Input:
```
2 3
```
Output:
```
5
```
'''
        problem, _ = Problem.objects.update_or_create(
            slug='sum-of-two-numbers',
            defaults={
                'title': 'Sum of Two Numbers',
                'difficulty': 'easy',
                'statement': statement,
                'time_ms': 1000,
                'memory_mb': 256,
                'status': 'published',
                'author': admin,
            },
        )
        for tag_name in ['math', 'implementation', 'warmup']:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            problem.tags.add(tag)

        TestCase.objects.filter(problem=problem).delete()
        for order, is_sample, input_data, expected_output in [
            (1, True, '2 3\n', '5\n'),
            (2, True, '-7 10\n', '3\n'),
            (3, False, '1000000000 234567890\n', '1234567890\n'),
            (4, False, '-50 -70\n', '-120\n'),
        ]:
            TestCase.objects.create(
                problem=problem,
                order=order,
                is_sample=is_sample,
                input=input_data,
                expected_output=expected_output,
            )
        return problem

    def _seed_contests(self, admin, problem):
        now = timezone.now()
        contests_data = [
            {
                'slug': 'codearena-demo-cup',
                'title': 'CodeArena Demo Cup',
                'description': 'A short public demo tournament for checking registration, problem access, and the scoreboard.',
                'contest_type': 'ICPC',
                'start_time': now - timedelta(minutes=30),
                'end_time': now + timedelta(hours=2),
                'freeze_time': now + timedelta(hours=1, minutes=15),
            },
            {
                'slug': 'newcomer-warmup-round',
                'title': 'Newcomer Warmup Round',
                'description': 'An upcoming beginner-friendly round with the same warmup problem.',
                'contest_type': 'CF',
                'start_time': now + timedelta(days=1),
                'end_time': now + timedelta(days=1, hours=2),
                'freeze_time': None,
            },
        ]
        contests = []
        for data in contests_data:
            contest, _ = Contest.objects.update_or_create(
                slug=data['slug'],
                defaults={**data, 'is_public': True, 'created_by': admin},
            )
            ContestProblem.objects.update_or_create(
                contest=contest,
                problem=problem,
                defaults={'order_label': 'A', 'points': 100},
            )
            contests.append(contest)
        return contests

    def _seed_participants(self, User, password):
        users = []
        for handle, email in [
            ('alice_demo', 'alice.demo@example.local'),
            ('bob_demo', 'bob.demo@example.local'),
            ('charlie_demo', 'charlie.demo@example.local'),
            ('dana_demo', 'dana.demo@example.local'),
            ('emir_demo', 'emir.demo@example.local'),
        ]:
            user, _ = User.objects.get_or_create(
                email=email,
                defaults={'handle': handle, 'role': 'user', 'is_active': True, 'is_verified': True},
            )
            user.handle = handle
            user.role = 'user'
            user.is_active = True
            user.is_verified = True
            user.is_banned = False
            user.set_password(password)
            user.save()
            users.append(user)
        return users

    def _seed_registrations(self, contests, users):
        active_contest, upcoming_contest = contests
        for user in users:
            ContestRegistration.objects.get_or_create(user=user, contest=active_contest)
        for user in users[:3]:
            ContestRegistration.objects.get_or_create(user=user, contest=upcoming_contest)

    def _seed_submissions(self, contest, problem, users):
        Submission.objects.filter(contest=contest, problem=problem, user__in=users).delete()
        submissions = [
            (users[0], 'AC', 42, 12000, "a,b=map(int,input().split())\nprint(a+b)\n"),
            (users[1], 'WA', 40, 11800, "a,b=map(int,input().split())\nprint(a-b)\n"),
            (users[1], 'AC', 45, 11920, "a,b=map(int,input().split())\nprint(a+b)\n"),
            (users[2], 'TLE', 1000, 20000, "while True:\n    pass\n"),
            (users[3], 'AC', 38, 11700, "print(sum(map(int,input().split())))\n"),
        ]
        for user, verdict, time_ms, memory_kb, code in submissions:
            Submission.objects.create(
                user=user,
                problem=problem,
                contest=contest,
                language='python',
                code=code,
                status='done',
                verdict=verdict,
                time_ms=time_ms,
                memory_kb=memory_kb,
            )
