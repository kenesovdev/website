from django.db.models import Q
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache

from apps.problems.permissions import IsAdminUser
from apps.users.authentication import BearerTokenAuthentication

from .models import Contest, ContestInvite, ContestRegistration
from .serializers import (
    ContestCreateSerializer,
    ContestDetailSerializer,
    ContestInviteSerializer,
    ContestListSerializer,
    ContestProblemSerializer,
)


class ContestPagination(PageNumberPagination):
    page_size = 20


class ContestViewSet(ModelViewSet):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = ContestPagination

    def get_queryset(self):
        qs = (
            Contest.objects.all()
            .select_related('created_by')
            .prefetch_related('contest_problems__problem', 'registrations')
            .order_by('-start_time')
        )
        user = self.request.user
        if user.role != 'admin':
            qs = qs.filter(
                Q(is_public=True)
                | Q(registrations__user=user)
                | Q(invites__user=user, invites__status='ACCEPTED')
            ).distinct()

        status_filter = self.request.query_params.get('status')
        if status_filter:
            status_map = {
                'UPCOMING': 'upcoming',
                'ONGOING': ('active', 'frozen'),
                'FINISHED': 'ended',
            }
            mapped = status_map.get(status_filter.upper())
            if mapped:
                if isinstance(mapped, tuple):
                    qs = [c for c in qs if c.status in mapped]
                else:
                    qs = [c for c in qs if c.status == mapped]
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if isinstance(queryset, list):
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'create':
            return ContestCreateSerializer
        if self.action == 'retrieve':
            return ContestDetailSerializer
        return ContestListSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'invite'):
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['POST'])
    def join(self, request, pk=None):
        contest = self.get_object()
        if contest.status == 'ended':
            return Response({'error': 'Соревнование завершено'}, status=400)

        if contest.participation_type == 'INVITE_ONLY':
            invite = ContestInvite.objects.filter(
                contest=contest, user=request.user,
            ).first()
            if not invite:
                raise PermissionDenied('Нет приглашения на это соревнование')
            if invite.status == 'PENDING':
                invite.status = 'ACCEPTED'
                invite.save(update_fields=['status'])
        elif contest.participation_type != 'OPEN':
            raise PermissionDenied('Невозможно присоединиться')

        ContestRegistration.objects.get_or_create(user=request.user, contest=contest)
        return Response({'status': 'joined'})

    @action(detail=True, methods=['POST'], url_path='register')
    def register(self, request, pk=None):
        """Alias for join — backward compatibility."""
        return self.join(request, pk=pk)

    @action(detail=True, methods=['POST'])
    def invite(self, request, pk=None):
        contest = self.get_object()
        if contest.participation_type != 'INVITE_ONLY':
            raise ValidationError({'detail': 'Приглашения доступны только для закрытых соревнований'})

        serializer = ContestInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        invite, created = ContestInvite.objects.get_or_create(
            contest=contest,
            user=user,
            defaults={'status': 'PENDING'},
        )
        if not created and invite.status == 'ACCEPTED':
            return Response({'status': 'already_accepted'})
        return Response({'status': 'invited', 'handle': user.handle})

    @action(detail=True, methods=['GET'], url_path='problems')
    def problems(self, request, pk=None):
        contest = self.get_object()
        is_reg = ContestRegistration.objects.filter(user=request.user, contest=contest).exists()
        if not (contest.is_public or is_reg or contest.status == 'ended' or request.user.role == 'admin'):
            raise PermissionDenied('Зарегистрируйтесь, чтобы видеть задачи')
        problems = contest.contest_problems.select_related('problem').order_by('order', 'order_label')
        return Response(
            ContestProblemSerializer(
                problems, many=True, context={'request': request, 'contest': contest},
            ).data,
        )

    @action(detail=True, methods=['GET'], url_path='standings')
    def standings(self, request, pk=None):
        contest = self.get_object()
        if contest.status == 'upcoming':
            raise PermissionDenied('Соревнование ещё не началось')

        admin_view = request.user.role == 'admin' and request.query_params.get('admin') == 'true'
        if contest.status == 'frozen' and not admin_view:
            snapshot = contest.snapshots.filter(snapshot_type='freeze').first()
            if snapshot:
                return Response(snapshot.data)

        cached = cache.get(f'scoreboard_live_{contest.id}')
        if cached:
            return Response(cached)

        from .scoreboard import calculate_scoreboard
        data = calculate_scoreboard(contest)
        cache.set(f'scoreboard_live_{contest.id}', data, timeout=30)
        return Response(data)

    @action(detail=True, methods=['GET'], url_path='scoreboard')
    def scoreboard(self, request, pk=None):
        """Alias for standings — backward compatibility."""
        return self.standings(request, pk=pk)
