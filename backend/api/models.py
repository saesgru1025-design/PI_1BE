import uuid
from django.db import models

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150, unique=True)
    password_hash = models.CharField(max_length=255)
    daily_hour_limit = models.IntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.name

class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return self.name

class Activity(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Alta'),
        (2, 'Media'),
        (3, 'Baja'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=50)
    due_date = models.DateField()
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3)
    status = models.CharField(max_length=30, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'activities'

    def __str__(self):
        return self.title

class Subtask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    scheduled_date = models.DateField()
    estimated_hours = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.CharField(max_length=30, default='pendiente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'subtasks'

    def __str__(self):
        return self.title

class ProgressLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subtask = models.ForeignKey(Subtask, on_delete=models.CASCADE, related_name='progress_logs')
    previous_status = models.CharField(max_length=30, null=True, blank=True)
    new_status = models.CharField(max_length=30)
    note = models.TextField(null=True, blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'progress_logs'

    def __str__(self):
        return f"{self.subtask.title} - {self.new_status}"

class RescheduleHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subtask = models.ForeignKey(Subtask, on_delete=models.CASCADE, related_name='reschedule_histories')
    old_date = models.DateField()
    new_date = models.DateField()
    reason = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reschedule_history'

    def __str__(self):
        return f"{self.subtask.title} - {self.old_date} -> {self.new_date}"

class DailyOverloadEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='overload_events')
    date = models.DateField()
    total_estimated_hours = models.DecimalField(max_digits=5, decimal_places=2)
    limit_hours = models.DecimalField(max_digits=5, decimal_places=2)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'daily_overload_events'

    def __str__(self):
        return f"Overload {self.user.name} - {self.date}"
