from rest_framework import serializers
from .models import Activity, Subtask, User, Subject
from datetime import date

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = '__all__'

    # 1. Candado: El nombre no puede estar vacío (Ojo: si tu variable se llama 'name', cambia 'title' por 'name' aquí abajo)
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("¡Error! El nombre de la subtarea no puede estar vacío.")
        return value

    # 2. Candado: Las horas no pueden ser 0 o negativas
    def validate_estimated_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError("¡Error! Las horas estimadas deben ser mayores a 0.")
        return value

    # 3. Candado: La fecha no puede estar en el pasado
    def validate_scheduled_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("¡La fecha de la subtarea no puede estar en el pasado!")
        return value


class ActivitySerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, read_only=True)

    class Meta:
        model = Activity
        fields = '__all__'

    # Validamos la fecha de la actividad principal
    def validate_due_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("¡Error! No puedes crear una actividad para un día que ya pasó.")
        return value