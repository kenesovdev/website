import pytest
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.contests.models import Contest, ContestProblem, ContestRegistration
from apps.problems.models import Problem
from apps.submissions.models import Submission
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='password')

@pytest.fixture
def problem():
    return Problem.objects.create(title='Test Problem', slug='test-problem', time_limit=1000, memory_limit=256)

@pytest.fixture
def contest(user):
    now = timezone.now()
    return Contest.objects.create(
        title='Test Contest',
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
        freeze_time=now + timedelta(minutes=30),
        created_by=user,
        is_public=True
    )

@pytest.fixture
def contest_problem(contest, problem):
    return ContestProblem.objects.create(contest=contest, problem=problem, order_label='A', points=100)

@pytest.fixture
def registered_user(user, contest):
    ContestRegistration.objects.create(user=user, contest=contest)
    return user

@pytest.mark.django_db
class TestContestSubmissionRules:
    
    def get_url(self):
        # We need to assume the url name for SubmissionListView.
        # It's usually something like 'submission-list' or we can just hardcode the path.
        return '/api/v1/submissions/'

    def test_submission_blocked_after_contest_ends(self, api_client, registered_user, contest, contest_problem):
        contest.end_time = timezone.now() - timedelta(hours=1)
        contest.start_time = timezone.now() - timedelta(hours=2)
        contest.save()
        
        api_client.force_authenticate(user=registered_user)
        response = api_client.post(self.get_url(), {
            'problem': contest_problem.problem.id,
            'code': 'print("hello")',
            'language': 'python',
            'contest_id': contest.id
        })
        assert response.status_code == 403
        assert 'ended' in str(response.data)

    def test_submission_blocked_if_not_registered(self, api_client, user, contest, contest_problem):
        api_client.force_authenticate(user=user)
        response = api_client.post(self.get_url(), {
            'problem': contest_problem.problem.id,
            'code': 'print("hello")',
            'language': 'python',
            'contest_id': contest.id
        })
        assert response.status_code == 403
        assert 'register' in str(response.data).lower()

    def test_submission_allowed_during_active_contest(self, api_client, registered_user, contest, contest_problem):
        api_client.force_authenticate(user=registered_user)
        response = api_client.post(self.get_url(), {
            'problem': contest_problem.problem.id,
            'code': 'print("hello")',
            'language': 'python',
            'contest_id': contest.id
        })
        assert response.status_code == 201
        assert Submission.objects.count() == 1
        assert Submission.objects.first().contest == contest
        assert not Submission.objects.first().is_after_freeze

    def test_submission_blocked_for_problem_not_in_contest(self, api_client, registered_user, contest, problem):
        # We don't create contest_problem here
        api_client.force_authenticate(user=registered_user)
        response = api_client.post(self.get_url(), {
            'problem': problem.id,
            'code': 'print("hello")',
            'language': 'python',
            'contest_id': contest.id
        })
        assert response.status_code == 400
        assert 'problem' in response.data

    def test_frozen_contest_sets_is_after_freeze_true(self, api_client, registered_user, contest, contest_problem):
        contest.freeze_time = timezone.now() - timedelta(minutes=10)
        contest.save()
        
        api_client.force_authenticate(user=registered_user)
        response = api_client.post(self.get_url(), {
            'problem': contest_problem.problem.id,
            'code': 'print("hello frozen")',
            'language': 'python',
            'contest_id': contest.id
        })
        assert response.status_code == 201
        assert Submission.objects.first().is_after_freeze is True

    def test_upcoming_contest_blocks_submission(self, api_client, registered_user, contest, contest_problem):
        contest.start_time = timezone.now() + timedelta(hours=1)
        contest.end_time = timezone.now() + timedelta(hours=2)
        contest.save()
        
        api_client.force_authenticate(user=registered_user)
        response = api_client.post(self.get_url(), {
            'problem': contest_problem.problem.id,
            'code': 'print("hello")',
            'language': 'python',
            'contest_id': contest.id
        })
        assert response.status_code == 403
        assert 'started' in str(response.data)

    @patch('apps.contests.tasks.recalculate_scoreboard.delay')
    def test_scoreboard_recalculate_task_called(self, mock_task, api_client, registered_user, contest, contest_problem):
        api_client.force_authenticate(user=registered_user)
        response = api_client.post(self.get_url(), {
            'problem': contest_problem.problem.id,
            'code': 'print("hello task")',
            'language': 'python',
            'contest_id': contest.id
        })
        assert response.status_code == 201
        mock_task.assert_called_once_with(contest.id)

    def test_normal_submission_without_contest_id_still_works(self, api_client, user, problem):
        api_client.force_authenticate(user=user)
        response = api_client.post(self.get_url(), {
            'problem': problem.id,
            'code': 'print("hello world")',
            'language': 'python'
        })
        assert response.status_code == 201
        submission = Submission.objects.first()
        assert submission.contest is None
        assert not submission.is_after_freeze
