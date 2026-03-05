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

Sprint 1 (Activities & Subtasks)

### 📌 1. Tabla de Endpoints

| Funcionalidad | Método | Ruta (Endpoint) | Descripción |
| :--- | :--- | :--- | :--- |
| **Listar / Crear Actividades** | `GET` / `POST` | `/api/activities/` | Obtiene todas las actividades o crea una nueva. |
| **Editar / Borrar Actividad** | `PUT` / `DELETE` | `/api/activities/<id>/` | Actualiza o elimina una actividad por su ID. |
| **Listar / Crear Subtareas** | `GET` / `POST` | `/api/subtasks/` | Obtiene todas las subtareas o crea una nueva. |
| **Editar / Borrar Subtarea** | `PUT` / `DELETE` | `/api/subtasks/<id>/` | Actualiza o elimina una subtarea por su ID. |

### 📥 2. Ejemplo de Request / Response (Crear Actividad)

* **Request (POST):**
  ```json
  {
    "title": "Aprender React",
    "due_date": "2026-12-01",
    "user": 1,
    "subject": 2
  }

Response (201 Created):
{
  "id": 5,
  "title": "Aprender React",
  "due_date": "2026-12-01",
  "user": 1,
  "subject": 2,
  "subtasks": []
}

### ⚠️ 3. Errores Estándar

* **Error 400 (Bad Request):** Falla en validaciones (ej. horas en 0).
  Ejemplo de respuesta:
  ```json
  {
    "estimated_hours": ["¡Error! Las horas estimadas deben ser mayores a 0."]
  }

Error 404 (Not Found): Se intentó acceder, editar o borrar un ID que no existe.
Ejemplo de respuesta:
{
  "detail": "No encontrado."
}
