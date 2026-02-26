from django.contrib import admin
from django.urls import path
from api.views import health_check  # <--- Aquí importamos tu vista

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),  # <--- Aquí creamos la ruta
]