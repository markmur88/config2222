from django.contrib.auth import authenticate
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from api.authentication.serializers import JWTTokenSerializer, UserSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)  # Configurar logger para depuración

class LoginView(views.APIView):
    permission_classes = [AllowAny]  # 🔥 Permite acceso sin autenticación
    
    @swagger_auto_schema(operation_description="User login")
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            logger.warning("Faltan credenciales en la solicitud de inicio de sesión.")
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if user:
            tokens = JWTTokenSerializer.get_tokens_for_user(user)
            logger.info(f"Inicio de sesión exitoso para el usuario: {username}")
            return Response(tokens, status=status.HTTP_200_OK)
        
        logger.warning(f"Credenciales inválidas para el usuario: {username}")
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(views.APIView):
    @swagger_auto_schema(operation_description="Get user profile")
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

