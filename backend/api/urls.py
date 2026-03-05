from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, SubtaskViewSet

# El Router crea las URLs automáticamente por nosotros
router = DefaultRouter()
router.register(r'activities', ActivityViewSet)
router.register(r'subtasks', SubtaskViewSet)

urlpatterns = [
    path('', include(router.urls)), # Dejamos esto vacío aquí porque le pondremos 'api/' en el archivo principal
]