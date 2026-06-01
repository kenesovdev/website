from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from .models import Contest, ContestRegistration
from .serializers import ContestListSerializer, ContestDetailSerializer, ContestProblemSerializer

class ContestViewSet(ModelViewSet):
    queryset = Contest.objects.all().select_related('created_by').prefetch_related('contest_problems__problem', 'registrations').order_by('-start_time')
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ContestDetailSerializer
        return ContestListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_public=True)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            # Post-filter by status property (upcoming/active/frozen/ended)
            qs = [c for c in qs if c.status == status_filter]
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['POST'])
    def register(self, request, pk=None):
        contest = self.get_object()
        if contest.status == 'ended':
            return Response({"error": "Ended"}, status=400)
        ContestRegistration.objects.get_or_create(user=request.user, contest=contest)
        return Response({"status": "registered"})

    @action(detail=True, methods=['POST'])
    def unregister(self, request, pk=None):
        contest = self.get_object()
        if contest.status != 'upcoming':
            return Response({"error": "Too late"}, status=400)
        ContestRegistration.objects.filter(user=request.user, contest=contest).delete()
        return Response(status=204)

    @action(detail=True, methods=['GET'], url_path='problems')
    def problems(self, request, pk=None):
        contest = self.get_object()
        is_reg = request.user.is_authenticated and ContestRegistration.objects.filter(user=request.user, contest=contest).exists()
        if not (contest.is_public or is_reg or contest.status == 'ended' or request.user.is_staff):
            raise PermissionDenied("Register to view problems")
        problems = contest.contest_problems.select_related('problem').order_by('order_label')
        return Response(ContestProblemSerializer(problems, many=True, context={'request': request, 'contest': contest}).data)

    @action(detail=True, methods=['GET'], url_path='scoreboard')
    def scoreboard(self, request, pk=None):
        contest = self.get_object()
        if contest.status == 'upcoming':
            raise PermissionDenied("Contest has not started")
        
        admin_view = request.user.is_staff and request.query_params.get('admin') == 'true'
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
