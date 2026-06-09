from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.problems.models import Problem
from apps.submissions.models import Submission

from .models import Contest, ContestInvite, ContestProblem, ContestRegistration, DIFFICULTY_XP

User = get_user_model()


class ProblemNestedSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    difficulty = serializers.CharField(read_only=True)
    time_limit = serializers.IntegerField(source='time_ms', read_only=True)
    memory_limit = serializers.IntegerField(source='memory_mb', read_only=True)


class ContestProblemSerializer(serializers.ModelSerializer):
    problem = ProblemNestedSerializer(read_only=True)
    user_result = serializers.SerializerMethodField()

    class Meta:
        model = ContestProblem
        fields = ['order_label', 'order', 'points', 'xp_reward', 'problem', 'user_result']

    def get_user_result(self, obj):
        request = self.context.get('request')
        contest = self.context.get('contest')
        if not request or not request.user.is_authenticated:
            return None

        qs_kwargs = {'user': request.user, 'problem': obj.problem}
        if hasattr(Submission, 'contest') and contest:
            qs_kwargs['contest'] = contest

        submissions = Submission.objects.filter(**qs_kwargs).order_by('-created_at')
        count = submissions.count()
        if count == 0:
            return None

        ac_submissions = submissions.filter(verdict='AC').order_by('created_at')
        if ac_submissions.exists():
            best_status = 'AC'
            first_ac = ac_submissions.first()
            ac_time_minutes = None
            if contest and contest.start_time:
                delta = first_ac.created_at - contest.start_time
                ac_time_minutes = int(delta.total_seconds() / 60)
        else:
            best_status = submissions.first().verdict or submissions.first().status
            ac_time_minutes = None

        return {
            'status': best_status,
            'attempts': count,
            'ac_time_minutes': ac_time_minutes,
        }


class ContestProblemInputSerializer(serializers.Serializer):
    problem_id = serializers.UUIDField()
    order = serializers.IntegerField(min_value=0, default=0)
    order_label = serializers.CharField(max_length=3, required=False)


class ContestCreateSerializer(serializers.ModelSerializer):
    problems = ContestProblemInputSerializer(many=True, required=False)

    class Meta:
        model = Contest
        fields = [
            'title', 'description', 'participation_type',
            'start_time', 'end_time', 'is_public', 'problems',
        ]

    def validate(self, attrs):
        if attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError({'end_time': 'Конец должен быть позже начала'})
        return attrs

    def create(self, validated_data):
        problems_data = validated_data.pop('problems', [])
        request = self.context['request']
        with transaction.atomic():
            contest = Contest.objects.create(created_by=request.user, **validated_data)
            for idx, item in enumerate(problems_data):
                try:
                    problem = Problem.objects.get(pk=item['problem_id'])
                except Problem.DoesNotExist:
                    raise serializers.ValidationError(
                        {'problems': f"Задача {item['problem_id']} не найдена"}
                    )
                order_label = item.get('order_label') or chr(ord('A') + idx)
                ContestProblem.objects.create(
                    contest=contest,
                    problem=problem,
                    order=item.get('order', idx),
                    order_label=order_label,
                    xp_reward=DIFFICULTY_XP.get(problem.difficulty, 50),
                    points=DIFFICULTY_XP.get(problem.difficulty, 50),
                )
        return contest


class ContestListSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    type = serializers.CharField(source='participation_type', read_only=True)
    participant_count = serializers.SerializerMethodField()
    problem_count = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            'id', 'title', 'slug', 'type', 'participation_type',
            'start_time', 'end_time', 'status', 'participant_count',
            'problem_count', 'is_registered',
        ]

    def get_status(self, obj):
        return obj.display_status

    def get_participant_count(self, obj):
        return obj.registrations.count()

    def get_problem_count(self, obj):
        return obj.contest_problems.count()

    def get_is_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ContestRegistration.objects.filter(user=request.user, contest=obj).exists()
        return False


class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'handle']


class ContestDetailSerializer(ContestListSerializer):
    description = serializers.CharField(read_only=True)
    created_by = UserNestedSerializer(read_only=True)
    problems = serializers.SerializerMethodField()

    class Meta(ContestListSerializer.Meta):
        fields = ContestListSerializer.Meta.fields + ['description', 'created_by', 'problems']

    def get_problems(self, obj):
        request = self.context.get('request')
        problems = obj.contest_problems.select_related('problem').order_by('order', 'order_label')
        return ContestProblemSerializer(
            problems, many=True, context={'request': request, 'contest': obj},
        ).data


class ContestInviteSerializer(serializers.Serializer):
    handle = serializers.CharField()

    def validate(self, attrs):
        try:
            attrs['user'] = User.objects.get(handle=attrs['handle'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'handle': 'Пользователь не найден'})
        return attrs
