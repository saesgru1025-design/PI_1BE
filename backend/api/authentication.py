import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User

logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    """
    Autenticación JWT personalizada que resuelve el user_id (UUID) del modelo
    'users' de Supabase en lugar del modelo Django por defecto.
    """

    def get_user(self, validated_token):
        user_id = validated_token.get('user_id') or validated_token.get('sub')

        if not user_id:
            logger.warning("Token JWT sin claim 'user_id' o 'sub'.")
            raise AuthenticationFailed(
                _("Token no contiene identificación de usuario válida"),
                code="token_invalid"
            )

        try:
            user = User.objects.get(id=user_id)
            return user
        except (User.DoesNotExist, TypeError, ValueError, Exception) as e:
            logger.error(f"Usuario con ID '{user_id}' no encontrado o ID inválido: {e}")
            raise AuthenticationFailed(
                _("Usuario no encontrado"),
                code="user_not_found"
            )
