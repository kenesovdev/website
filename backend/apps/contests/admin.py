from django.contrib import admin
from .models import Contest, ContestProblem, ContestRegistration, ScoreboardSnapshot


class ContestProblemInline(admin.TabularInline):
    model = ContestProblem
    extra = 3


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ['title', 'contest_type', 'start_time', 'end_time', 'is_public']
    list_filter = ['contest_type', 'is_public']
    search_fields = ['title']
    inlines = [ContestProblemInline]


@admin.register(ContestRegistration)
class ContestRegistrationAdmin(admin.ModelAdmin):
    list_display = ['user', 'contest', 'registered_at']
    list_filter = ['contest']
    search_fields = ['user__email', 'user__handle', 'contest__title']


@admin.register(ScoreboardSnapshot)
class ScoreboardSnapshotAdmin(admin.ModelAdmin):
    list_display = ['contest', 'snapshot_type', 'taken_at']
    list_filter = ['snapshot_type', 'contest']
    search_fields = ['contest__title']
