from django.http import JsonResponse
from rest_framework import viewsets
from .models import Activity, Subtask
from .serializers import ActivitySerializer, SubtaskSerializer

# 1. El Health Check que hizo tu compañero (para que no dé error)
def health_check(request):
    return JsonResponse({"status": "ok", "message": "Backend funcionando al 100%"})

# 2. Tu Vista para las Actividades (Sprint 1)
class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

# 3. Tu Vista para las Subtareas (Sprint 1)
class SubtaskViewSet(viewsets.ModelViewSet):
    queryset = Subtask.objects.all()
    serializer_class = SubtaskSerializer