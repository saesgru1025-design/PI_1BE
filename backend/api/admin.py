from django.contrib import admin
from .models import (
    User, Subject, Activity, Subtask,
    ProgressLog, RescheduleHistory, DailyOverloadEvent
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'daily_hour_limit', 'created_at')
    search_fields = ('name', 'email')
    ordering = ('-created_at',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'color', 'created_at')
    search_fields = ('name',)
    list_filter = ('user',)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'subject', 'type', 'due_date', 'priority', 'status', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('status', 'priority', 'type')
    ordering = ('-created_at',)

@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'activity', 'scheduled_date', 'estimated_hours', 'status')
    search_fields = ('title',)
    list_filter = ('status',)
    ordering = ('scheduled_date',)

@admin.register(ProgressLog)
class ProgressLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'subtask', 'previous_status', 'new_status', 'logged_at')
    ordering = ('-logged_at',)

@admin.register(RescheduleHistory)
class RescheduleHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'subtask', 'old_date', 'new_date', 'created_at')
    ordering = ('-created_at',)

@admin.register(DailyOverloadEvent)
class DailyOverloadEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date', 'total_estimated_hours', 'limit_hours', 'resolved', 'created_at')
    list_filter = ('resolved',)
    ordering = ('-date',)
