from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, exceptions, viewsets, serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

from .models import User, Activity, Subtask


@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "¡Hola profesor la API está FUNCIONANDO!"
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

        # Soporta hash de Django y contraseñas en texto plano (migración legada)
        is_correct = check_password(password, user.password_hash) or user.password_hash == password

        if not is_correct:
            logger.warning(f"Intento de login fallido: contraseña incorrecta para {email}")
            raise exceptions.AuthenticationFailed('Contraseña incorrecta')

        # Generar tokens con claim user_id explícito en ambos (refresh y access)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken()
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


# ─── ACTIVITIES ───────────────────────────────────────────────────────────────

class ActivityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import ActivitySerializer
        return ActivitySerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not hasattr(user, 'id'):
            return Activity.objects.none()
        return Activity.objects.filter(user_id=user.id).order_by('-created_at')

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
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from .serializers import SubtaskSerializer
        return SubtaskSerializer

    def get_queryset(self):
        user = self.request.user
        if not user or not hasattr(user, 'id'):
            return Subtask.objects.none()

        queryset = Subtask.objects.filter(activity__user_id=user.id)

        activity_id = self.request.query_params.get('activity')
        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)

        return queryset

    def perform_create(self, serializer):
        subtask = serializer.save()
        self._check_daily_limit(subtask)

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

        self._check_daily_limit(updated)

    def _check_daily_limit(self, subtask):
        try:
            user = subtask.activity.user
            date = subtask.scheduled_date

            from django.db.models import Sum
            from .models import DailyOverloadEvent

            total_hours = Subtask.objects.filter(
                activity__user=user,
                scheduled_date=date
            ).aggregate(Sum('estimated_hours'))['estimated_hours__sum'] or 0

            if total_hours > user.daily_hour_limit:
                DailyOverloadEvent.objects.get_or_create(
                    user=user,
                    date=date,
                    defaults={
                        'total_estimated_hours': total_hours,
                        'limit_hours': user.daily_hour_limit,
                        'resolved': False
                    }
                )
        except Exception as e:
            logger.error(f"Error al verificar límite diario: {e}")


# ─── REGISTRO ─────────────────────────────────────────────────────────────────

class RegisterUserView(APIView):
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
        refresh = RefreshToken()
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