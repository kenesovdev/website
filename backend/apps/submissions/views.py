from django.core.cache import cache
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.problems.models import Problem
from apps.users.authentication import BearerTokenAuthentication

from .models import Submission
from .pagination import SubmissionPagination
from .runner import run_sample_tests
from .serializers import (
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    SubmissionListSerializer,
    TestRunSerializer,
)


class SubmissionListView(generics.ListCreateAPIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = SubmissionPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubmissionCreateSerializer
        return SubmissionListSerializer

    def get_queryset(self):
        qs = Submission.objects.filter(user=self.request.user).select_related('problem', 'user')
        
        # Filter by problem ID
        problem_id = self.request.query_params.get('problem')
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
            
        # Filter by problem slug
        problem_slug = self.request.query_params.get('problem_slug')
        if problem_slug:
            qs = qs.filter(problem__slug=problem_slug)
            
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        # Ordering support
        ordering = self.request.query_params.get('ordering')
        if ordering:
            allowed_orderings = {'time_ms', '-time_ms', 'created_at', '-created_at'}
            order_fields = [f.strip() for f in ordering.split(',')]
            valid_order_fields = [f for f in order_fields if f in allowed_orderings]
            if valid_order_fields:
                qs = qs.order_by(*valid_order_fields)
            else:
                qs = qs.order_by('-created_at')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def perform_create(self, serializer):
        from apps.contests.models import Contest, ContestProblem, ContestRegistration
        from django.db import transaction
        from django.utils import timezone
        from rest_framework.exceptions import ValidationError, PermissionDenied

        contest = None
        is_after_freeze = False
        contest_id = self.request.data.get('contest_id')

        if contest_id:
            # 1. Contest must exist
            try:
                contest = Contest.objects.get(id=contest_id)
            except Contest.DoesNotExist:
                raise ValidationError({'contest_id': 'Contest not found'})

            # 2. Contest must be active (not upcoming, not ended)
            if contest.status == 'upcoming':
                raise PermissionDenied('Contest has not started yet')
            if contest.status == 'ended':
                raise PermissionDenied('Contest has ended — submissions are closed')

            # 3. User must be registered
            if not ContestRegistration.objects.filter(
                user=self.request.user, contest=contest
            ).exists():
                raise PermissionDenied('You must register for the contest to submit')

            # 4. Problem must be part of the contest
            problem = serializer.validated_data.get('problem')
            if problem and not ContestProblem.objects.filter(
                contest=contest, problem=problem
            ).exists():
                raise ValidationError({'problem': 'This problem is not in the contest'})

            # 5. Mark if after freeze
            if contest.freeze_time and timezone.now() >= contest.freeze_time:
                is_after_freeze = True

        submission = serializer.save(
            user=self.request.user,
            status='pending',
            contest=contest,
            is_after_freeze=is_after_freeze
        )

        # Trigger scoreboard recalculation after DB commit
        if contest:
            try:
                from apps.contests.tasks import recalculate_scoreboard
                enqueue_scoreboard = lambda: recalculate_scoreboard.delay(contest.id)
                if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
                    enqueue_scoreboard()
                else:
                    transaction.on_commit(enqueue_scoreboard)
            except ImportError:
                pass # In case tasks is not defined yet
                
        return submission

    def create(self, request, *args, **kwargs):
        serializer = SubmissionCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        submission = self.perform_create(serializer)
        output = SubmissionDetailSerializer(submission)
        return Response(output.data, status=status.HTTP_201_CREATED)


class SubmissionDetailView(generics.RetrieveAPIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionDetailSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Submission.objects.all()
        return Submission.objects.filter(user=self.request.user)


class TestRunView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cache_key = f'submission_test_run:{request.user.pk}'
        if cache.get(cache_key):
            return Response(
                {'detail': 'Rate limit: one test run per 10 seconds.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        serializer = TestRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        problem = get_object_or_404(
            Problem,
            pk=serializer.validated_data['problem_id'],
            status='published',
        )
        results = run_sample_tests(
            problem=problem,
            code=serializer.validated_data['code'],
            language=serializer.validated_data['language'],
            timeout=5.0,
        )
        cache.set(cache_key, True, timeout=10)
        return Response({'results': results})
