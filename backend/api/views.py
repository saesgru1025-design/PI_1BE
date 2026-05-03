from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, exceptions, viewsets, serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.permissions import IsAuthenticated, AllowAny
import logging

logger = logging.getLogger(__name__)

from .models import User, Activity, Subtask, Subject


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "¡API StudyCleaner v1.1.0 FUNCIONANDO!",
        "version": "1.1.0"
    })


# ─── AUTH ────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer de login que usa el modelo User personalizado (tabla 'users' en Supabase).
    Acepta email + password y devuelve tokens JWT con claim user_id explícito.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip()
        password = attrs.get('password', '')

        if not email or not password:
            raise exceptions.AuthenticationFailed('Email y contraseña son requeridos')

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            logger.warning(f"Intento de login fallido: usuario {email} no encontrado")
            raise exceptions.AuthenticationFailed('Usuario no encontrado')

        is_correct = check_password(password, user.password_hash) or user.password_hash == password

        if not is_correct:
            logger.warning(f"Intento de login fallido: contraseña incorrecta para {email}")
            raise exceptions.AuthenticationFailed('Contraseña incorrecta')

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh['user_id'] = str(user.id)

        access = refresh.access_token
        access['user_id'] = str(user.id)

        logger.info(f"Login exitoso para usuario: {email} ({user.id})")

        return {
            'refresh': str(refresh),
            'access': str(access),
            'user': {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'daily_hour_limit': user.daily_hour_limit,
            }
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except exceptions.AuthenticationFailed as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


# ─── PERFIL DE USUARIO ────────────────────────────────────────────────────────

class UserProfileView(APIView):
    """
    Perfil y configuración del usuario autenticado.

    Endpoints:
      GET   /api/auth/me/   → Devuelve perfil y límite diario actual
      PATCH /api/auth/me/   → Actualiza daily_hour_limit (entre 1 y 24 h)

    Body para PATCH:
      { "daily_hour_limit": 8 }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'daily_hour_limit': user.daily_hour_limit,
        })

    def patch(self, request):
        user = request.user
        limit = request.data.get('daily_hour_limit')
        name = request.data.get('name')
        email = request.data.get('email')

        update_fields = []

        if limit is not None:
            try:
                limit = int(limit)
                if 1 <= limit <= 24:
                    user.daily_hour_limit = limit
                    update_fields.append('daily_hour_limit')
                else:
                    return Response({'error': 'El límite debe estar entre 1 y 24 horas'}, status=status.HTTP_400_BAD_REQUEST)
            except (TypeError, ValueError):
                return Response({'error': 'Valor inválido para daily_hour_limit'}, status=status.HTTP_400_BAD_REQUEST)

        if name:
            user.name = name.strip()
            update_fields.append('name')

        if email:
            email = email.strip()
            if User.objects.filter(email__iexact=email).exclude(id=user.id).exists():
                return Response({'error': 'Este email ya está en uso por otro usuario'}, status=status.HTTP_400_BAD_REQUEST)
            user.email = email
            update_fields.append('email')

        if not update_fields:
            return Response({'error': 'No se proporcionaron campos para actualizar'}, status=status.HTTP_400_BAD_REQUEST)

        user.save(update_fields=update_fields)
        logger.info(f"Usuario {user.id} actualizó perfil: {', '.join(update_fields)}")

        return Response({
            'id': str(user.id),
            'name': user.name,
            'email': user.email,
            'daily_hour_limit': user.daily_hour_limit,
        })


# ─── SUBJECTS ─────────────────────────────────────────────────────────────────

class SubjectViewSet(viewsets.ModelViewSet):
    """
    CRUD de materias/asignaturas del usuario autenticado.

    Endpoints:
      GET    /api/subjects/          → Lista todas las materias del usuario
      POST   /api/subjects/          → Crea una nueva materia
      GET    /api/subjects/{id}/     → Detalle de una materia
      PATCH  /api/subjects/{id}/     → Actualización parcial
      PUT    /api/subjects/{id}/     → Actualización completa
      DELETE /api/subjects/{id}/     → Eliminar materia (y sus actividades en cascade)

    Body requerido para crear:
      { "name": "Matemáticas", "color": "#6366f1" }
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import SubjectSerializer
        return SubjectSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not hasattr(user, 'id'):
            return Subject.objects.none()
        return Subject.objects.filter(user_id=user.id).order_by('name')

    def perform_create(self, serializer):
        logger.info(f"Creando materia para usuario {self.request.user.id}")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save()


# ─── ACTIVITIES ───────────────────────────────────────────────────────────────

class ActivityViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de actividades/tareas del usuario autenticado.

    Endpoints:
      GET    /api/activities/          → Lista actividades. Soporta filtros:
                                          ?status=pendiente|en progreso|completada
                                          ?priority=1|2|3
                                          ?upcoming=true  (próximas 7 días)
                                          ?subject={uuid}
      POST   /api/activities/          → Crea una nueva actividad
      GET    /api/activities/{id}/     → Detalle de una actividad
      PATCH  /api/activities/{id}/     → Actualización parcial (ej: solo status)
      PUT    /api/activities/{id}/     → Actualización completa
      DELETE /api/activities/{id}/     → Eliminar actividad (subtareas en cascade)

    Body requerido para crear:
      {
        "title": "Estudiar para parcial",
        "type": "estudio|tarea|examen|proyecto|otro",
        "due_date": "2025-04-15",
        "priority": 1,           (1=Alta, 2=Media, 3=Baja)
        "status": "pendiente",   (pendiente|en progreso|completada)
        "subject": "uuid",       (opcional)
        "description": "..."     (opcional)
      }
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import ActivitySerializer
        return ActivitySerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not hasattr(user, 'id'):
            return Activity.objects.none()

        queryset = Activity.objects.filter(user_id=user.id).order_by('-created_at')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        subject_filter = self.request.query_params.get('subject')
        if subject_filter:
            queryset = queryset.filter(subject_id=subject_filter)

        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            from datetime import date, timedelta
            today = date.today()
            next_week = today + timedelta(days=7)
            queryset = queryset.filter(due_date__gte=today, due_date__lte=next_week)

        return queryset

    def perform_create(self, serializer):
        data = serializer.validated_data
        if 'subject' in data and not data['subject']:
            data['subject'] = None
        logger.info(f"Guardando actividad '{data.get('title')}' para usuario {self.request.user.id}")
        try:
            serializer.save(user=self.request.user)
        except Exception as e:
            logger.error(f"Error al crear actividad: {e}")
            raise


# ─── SUBTASKS ─────────────────────────────────────────────────────────────────

class SubtaskViewSet(viewsets.ModelViewSet):
    """
    CRUD de subtareas asociadas a una actividad.

    Endpoints:
      GET    /api/subtasks/             → Lista subtareas. Filtros:
                                           ?activity={uuid}  (filtrar por actividad)
      POST   /api/subtasks/             → Crear subtarea
      GET    /api/subtasks/{id}/        → Detalle
      PATCH  /api/subtasks/{id}/        → Actualización parcial (ej: cambiar status)
      PUT    /api/subtasks/{id}/        → Actualización completa
      DELETE /api/subtasks/{id}/        → Eliminar subtarea
      GET    /api/subtasks/hoy/         → Subtareas programadas para hoy + info de carga
      POST   /api/subtasks/{id}/mover/  → Mover subtarea al día siguiente (C4: resolución de conflicto)

    Body requerido para crear:
      {
        "activity": "uuid-actividad",
        "title": "Leer capítulo 3",
        "scheduled_date": "2025-04-10",
        "estimated_hours": 2.5,
        "status": "pendiente",    (pendiente|en progreso|completada)
        "description": "..."      (opcional)
      }

    Efectos secundarios automáticos:
      - Al cambiar status → se crea un ProgressLog
      - Al cambiar scheduled_date → se crea un RescheduleHistory
      - Al crear/actualizar → verifica límite diario y gestiona DailyOverloadEvent
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import SubtaskSerializer
        return SubtaskSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not hasattr(user, 'id'):
            return Subtask.objects.none()

        queryset = Subtask.objects.filter(activity__user_id=user.id).select_related('activity')

        activity_id = self.request.query_params.get('activity')
        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)

        return queryset

    def perform_create(self, serializer):
        subtask = serializer.save()
        self._check_daily_limit(subtask)
        # Avisar al frontend que hubo un cambio de subtareas
        logger.info(f"Subtarea '{subtask.title}' creada para fecha {subtask.scheduled_date}")

    def perform_update(self, serializer):
        instance = self.get_object()
        old_status = instance.status
        old_date = instance.scheduled_date

        updated = serializer.save()

        # Registrar cambio de estado
        if old_status != updated.status:
            from .models import ProgressLog
            ProgressLog.objects.create(
                subtask=updated,
                previous_status=old_status,
                new_status=updated.status,
                note="Status actualizado desde la web"
            )

        # Registrar reprogramación
        if old_date != updated.scheduled_date:
            from .models import RescheduleHistory
            RescheduleHistory.objects.create(
                subtask=updated,
                old_date=old_date,
                new_date=updated.scheduled_date,
                reason="Fecha cambiada desde la web"
            )
            # Recalcular sobrecarga para la fecha anterior
            self._recalculate_overload(updated.activity.user, old_date)

        self._check_daily_limit(updated)

    # ── Acción: subtareas de hoy ─────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='hoy')
    def hoy(self, request):
        """
        GET /api/subtasks/hoy/
        Devuelve las subtareas del usuario programadas para la fecha de hoy,
        junto con la carga horaria total y si se supera el límite diario (C1, C3).
        Soporta ?date=YYYY-MM-DD para manejar zonas horarias.
        """
        from datetime import date
        from django.db.models import Sum
        from .models import DailyOverloadEvent

        date_str = request.query_params.get('date')
        if date_str:
            try:
                today = date.fromisoformat(date_str)
            except (ValueError, TypeError):
                today = date.today()
        else:
            today = date.today()

        user = request.user

        subtasks = Subtask.objects.filter(
            activity__user_id=user.id,
            scheduled_date=today
        ).select_related('activity').order_by('status', 'activity__title', 'title')

        total_hours = subtasks.aggregate(Sum('estimated_hours'))['estimated_hours__sum'] or 0
        total_hours = float(total_hours)
        limit = float(user.daily_hour_limit)
        overloaded = total_hours > limit

        from .serializers import SubtaskSerializer
        serializer = SubtaskSerializer(subtasks, many=True)

        return Response({
            'date': str(today),
            'subtasks': serializer.data,
            'total_hours': round(total_hours, 2),
            'limit_hours': limit,
            'overloaded': overloaded,
            'excess_hours': round(max(0.0, total_hours - limit), 2),
        })

    # ── Acción: mover al día siguiente (C4: resolución de conflicto) ─────────

    @action(detail=True, methods=['post'], url_path='mover')
    def mover(self, request, pk=None):
        """
        POST /api/subtasks/{id}/mover/
        Mueve la subtarea al día siguiente para resolver una sobrecarga (C4).
        Registra el cambio en RescheduleHistory y actualiza DailyOverloadEvent.
        """
        from datetime import timedelta
        from .models import RescheduleHistory

        subtask = self.get_object()
        old_date = subtask.scheduled_date
        new_date = old_date + timedelta(days=1)

        subtask.scheduled_date = new_date
        subtask.save(update_fields=['scheduled_date', 'updated_at'])

        # Bitácora de reprogramación
        RescheduleHistory.objects.create(
            subtask=subtask,
            old_date=old_date,
            new_date=new_date,
            reason="Movida al día siguiente — resolución automática de sobrecarga"
        )

        # Recalcular sobrecarga para la fecha original
        self._recalculate_overload(subtask.activity.user, old_date)

        # Verificar nueva fecha
        self._check_daily_limit(subtask)

        logger.info(f"Subtarea '{subtask.title}' movida de {old_date} a {new_date}")

        from .serializers import SubtaskSerializer
        return Response({
            'subtask': SubtaskSerializer(subtask).data,
            'old_date': str(old_date),
            'new_date': str(new_date),
            'message': f'Subtarea movida al {new_date.strftime("%d/%m/%Y")}'
        })

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _check_daily_limit(self, subtask):
        """Crea o actualiza DailyOverloadEvent si la carga del día supera el límite."""
        try:
            from django.db.models import Sum
            from .models import DailyOverloadEvent

            user = subtask.activity.user
            target_date = subtask.scheduled_date

            total_hours = Subtask.objects.filter(
                activity__user=user,
                scheduled_date=target_date
            ).aggregate(Sum('estimated_hours'))['estimated_hours__sum'] or 0
            total_hours = float(total_hours)
            limit = float(user.daily_hour_limit)

            if total_hours > limit:
                event, created = DailyOverloadEvent.objects.get_or_create(
                    user=user,
                    date=target_date,
                    defaults={
                        'total_estimated_hours': total_hours,
                        'limit_hours': limit,
                        'resolved': False
                    }
                )
                if not created:
                    event.total_estimated_hours = total_hours
                    event.limit_hours = limit
                    event.resolved = False
                    event.save(update_fields=['total_estimated_hours', 'limit_hours', 'resolved'])
            else:
                # Ya no hay sobrecarga: marcar como resuelto
                DailyOverloadEvent.objects.filter(
                    user=user, date=target_date, resolved=False
                ).update(resolved=True)

        except Exception as e:
            logger.error(f"Error al verificar límite diario: {e}")

    def _recalculate_overload(self, user, target_date):
        """Recalcula y actualiza el estado de sobrecarga para una fecha dada."""
        try:
            from django.db.models import Sum
            from .models import DailyOverloadEvent

            total_hours = Subtask.objects.filter(
                activity__user=user,
                scheduled_date=target_date
            ).aggregate(Sum('estimated_hours'))['estimated_hours__sum'] or 0
            total_hours = float(total_hours)
            limit = float(user.daily_hour_limit)

            if total_hours <= limit:
                DailyOverloadEvent.objects.filter(
                    user=user, date=target_date, resolved=False
                ).update(resolved=True)
            else:
                DailyOverloadEvent.objects.filter(
                    user=user, date=target_date
                ).update(total_estimated_hours=total_hours, resolved=False)

        except Exception as e:
            logger.error(f"Error al recalcular sobrecarga: {e}")


# ─── SOBRECARGA (OVERLOAD EVENTS) ─────────────────────────────────────────────

@api_view(['GET'])
def overload_list(request):
    """
    GET /api/overload/
    Lista los eventos de sobrecarga activos (no resueltos) del usuario autenticado.
    Útil para mostrar un resumen de días con conflicto de horario (C3).
    """
    from .models import DailyOverloadEvent

    events = DailyOverloadEvent.objects.filter(
        user=request.user,
        resolved=False
    ).order_by('date')[:30]

    result = [{
        'id': str(e.id),
        'date': str(e.date),
        'total_estimated_hours': float(e.total_estimated_hours),
        'limit_hours': float(e.limit_hours),
        'excess_hours': round(float(e.total_estimated_hours) - float(e.limit_hours), 2),
        'resolved': e.resolved,
        'created_at': e.created_at.isoformat(),
    } for e in events]

    return Response(result)


# ─── REGISTRO ─────────────────────────────────────────────────────────────────

class RegisterUserView(APIView):
    """
    Registro de nuevos usuarios.

    Endpoint: POST /api/auth/register/
    Body: { "name": "...", "email": "...", "password": "..." }
    Respuesta: { user: {...}, access: "jwt", refresh: "jwt" }
    """
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '')
        name = request.data.get('name', '').strip()

        if not email or not password or not name:
            return Response({'error': 'Todos los campos son obligatorios'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'El email ya está registrado'}, status=status.HTTP_400_BAD_REQUEST)

        password_hash = make_password(password)

        user = User.objects.create(
            email=email,
            name=name,
            password_hash=password_hash
        )

        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh['user_id'] = str(user.id)

        access = refresh.access_token
        access['user_id'] = str(user.id)

        logger.info(f"Usuario registrado exitosamente: {email}")

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'name': user.name,
                'daily_hour_limit': user.daily_hour_limit,
            },
            'access': str(access),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)