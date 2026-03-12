from rest_framework import serializers
from .models import Activity, Subtask, Subject


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
            'due_date': {'required': False},
            'priority': {'required': False, 'default': 3},
            'status': {'required': False, 'default': 'pendiente'},
        }

    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None

    def get_subject_color(self, obj):
        return obj.subject.color if obj.subject else None

    def validate(self, attrs):
        if 'due_date' not in attrs or not attrs.get('due_date'):
            from datetime import date
            attrs['due_date'] = date.today()
        if 'type' not in attrs or not attrs.get('type'):
            attrs['type'] = 'tarea'
        return attrs


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
            'estimated_hours': {'required': False, 'default': 1.0},
        }

    def validate(self, attrs):
        from datetime import date
        if 'scheduled_date' not in attrs or not attrs.get('scheduled_date'):
            attrs['scheduled_date'] = date.today()
        if 'estimated_hours' not in attrs or not attrs.get('estimated_hours'):
            attrs['estimated_hours'] = 1.0
        return attrs
