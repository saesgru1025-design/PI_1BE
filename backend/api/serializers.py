from rest_framework import serializers
from .models import Activity, Subtask


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            'id', 'user', 'subject', 'title', 'description',
            'type', 'due_date', 'priority', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
        extra_kwargs = {
            'subject': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'type': {'required': False, 'default': 'tarea'},
            'priority': {'required': False, 'default': 3},
            'status': {'required': False, 'default': 'pendiente'},
        }


class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = [
            'id', 'activity', 'title', 'description',
            'scheduled_date', 'estimated_hours', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True},
            'status': {'required': False, 'default': 'pendiente'},
        }
