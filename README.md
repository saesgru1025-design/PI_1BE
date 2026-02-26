# Backend - 

Este es el backend del proyecto integrador, construido con Django y Django Rest Framework.

# Cómo inicializar y ejecutar el proyecto (Local)

1. Crear y activar el entorno virtual:
   `python -m venv venv`
   `venv\Scripts\activate` (En Windows)
2. Instalar dependencias:
   `pip install -r requirements.txt`
3. Ejecutar el servidor:
   `python manage.py runserver`

##  Contrato de Endpoints / JSON base

### Health Check
Comprueba que la API esté viva y respondiendo.
- **URL:** `/api/health/`
- **Método:** `GET`
- **Respuesta Exitosa (200 OK):**
```json
{
    "status": "ok",
    "message": "¡Hola profesor la API  está FUNCIONANDO!"
}