from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import exceptions, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import User, Activity, Subtask
from .serializers import ActivitySerializer, SubtaskSerializer

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "ok", 
        "message": "¡Hola profesor la API  está FUNCIONANDO!"
    })

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = self.fields['username']
        del self.fields['username']

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('No active account found with the given credentials')

        if not check_password(password, user.password_hash) and user.password_hash != password:
            raise exceptions.AuthenticationFailed('No active account found with the given credentials')

        refresh = self.get_token(user)

        data = {}
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data

    @classmethod
    def get_token(cls, user):
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken()
        token['user_id'] = str(user.id)
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class ActivityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ActivitySerializer

    def get_queryset(self):
        user_id = self.request.user.id
        return Activity.objects.filter(user_id=user_id)

class SubtaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubtaskSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        return Subtask.objects.filter(activity__user_id=user_id)

class RegisterUserView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')

        if not email or not password or not name:
            return Response({'error': 'Todos los campos son obligatorios'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'El email ya está registrado'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Hashear password antes de pasarlo al modelo
        password_hash = make_password(password)

        # Crear en Supabase mediante el ORM
        user = User.objects.create(
            email=email,
            name=name,
            password_hash=password_hash
        )

        # Retornar sus tokens JWT iniciales para que el UX sea automatizado (login al registrar)
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken()
        refresh['user_id'] = str(user.id)

        return Response({
            'user': {
                'id': str(user.id),
                'email': user.email,
                'name': user.name
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_201_CREATED)