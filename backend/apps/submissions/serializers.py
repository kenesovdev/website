from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Submission


class SubmissionCreateSerializer(serializers.ModelSerializer):
    contest_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Submission
        fields = ('problem', 'code', 'language', 'contest_id')

    def validate(self, attrs):
        request = self.context['request']
        one_second_ago = timezone.now() - timedelta(seconds=1)
        duplicate = Submission.objects.filter(
            user=request.user,
            problem=attrs['problem'],
            code=attrs['code'],
            created_at__gte=one_second_ago,
        ).exists()
        if duplicate:
            raise serializers.ValidationError(
                'Duplicate submission: same code was submitted within the last second.',
            )
        return attrs


class SubmissionListSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Submission
        fields = [
            'id', 'problem_title', 'problem_slug', 'username',
            'language', 'status', 'verdict',
            'time_ms', 'memory_kb', 'created_at',
        ]


class SubmissionDetailSerializer(SubmissionListSerializer):
    contest = serializers.SerializerMethodField()
    is_after_freeze = serializers.BooleanField(read_only=True)

    class Meta(SubmissionListSerializer.Meta):
        fields = SubmissionListSerializer.Meta.fields + ['code', 'contest', 'is_after_freeze']

    def get_contest(self, obj):
        if obj.contest:
            return {'id': obj.contest.id, 'title': obj.contest.title, 'slug': obj.contest.slug}
        return None


class TestRunSerializer(serializers.Serializer):
    problem_id = serializers.UUIDField()
    code = serializers.CharField()
    language = serializers.ChoiceField(choices=['python', 'cpp', 'java'])
