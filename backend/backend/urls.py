from django.contrib import admin
from django.urls import path, include
from api.views import health_check 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    # Aquí llamamos al archivo de arriba
    path('api/', include('api.urls')), 
]