from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from api.views import (
    health_check, 
    CustomTokenObtainPairView,
    ActivityViewSet,
    SubtaskViewSet,
    RegisterUserView
)

router = DefaultRouter()
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'subtasks', SubtaskViewSet, basename='subtask')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),  # <--- Aquí creamos la ruta
    path('api/auth/register/', RegisterUserView.as_view(), name='register'),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include(router.urls)),
]