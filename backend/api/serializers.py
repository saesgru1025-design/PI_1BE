from rest_framework import serializers
from .models import Activity, Subtask, Subject
from datetime import date

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'color': {'required': False, 'allow_null': True, 'allow_blank': True},
        }


class ActivitySerializer(serializers.ModelSerializer):
    subject_name = serializers.SerializerMethodField()
    subject_color = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            'id', 'user', 'subject', 'subject_name', 'subject_color',
            'title', 'description', 'type', 'due_date',
            'priority', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'subject_name', 'subject_color']
        extra_kwargs = {
            'subject': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'type': {'required': False, 'default': 'tarea'},
            'due_date': {'required': False, 'default': date.today},
            'priority': {'required': False, 'default': 3},
            'status': {'required': False, 'default': 'pendiente'},
        }

    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None

    def get_subject_color(self, obj):
        return obj.subject.color if obj.subject else None


class SubtaskSerializer(serializers.ModelSerializer):
    activity_title = serializers.CharField(source='activity.title', read_only=True)
    activity_type  = serializers.CharField(source='activity.type',  read_only=True)

    class Meta:
        model = Subtask
        fields = [
            'id', 'activity', 'activity_title', 'activity_type',
            'title', 'description',
            'scheduled_date', 'estimated_hours', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'activity_title', 'activity_type']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'status': {'required': False, 'default': 'pendiente'},
            'scheduled_date': {'required': False, 'default': date.today},
            'estimated_hours': {'required': False, 'default': 1.0},
        }
