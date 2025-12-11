"""
Helpers para autenticación JWT
"""
import jwt
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from .models import Usuario

def obtener_usuario_desde_token(request):
    """
    Extrae y valida el token JWT del header Authorization.
    Retorna el usuario si es válido, None si no.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    
    try:
        decoded = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=['HS256']
        )
        user_id = decoded.get('userId')
        if user_id:
            return Usuario.objects.get(id=user_id, activo=True)
    except (jwt.DecodeError, jwt.InvalidSignatureError, Usuario.DoesNotExist):
        return None
    
    return None

def generar_token_jwt(usuario):
    """
    Genera un token JWT con claims de correo, rol y userId.
    """
    payload = {
        'correo': usuario.correo,
        'rol': usuario.rol,
        'userId': usuario.id
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
    # Asegurar que retorne string (PyJWT puede retornar bytes en algunas versiones)
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token

def requiere_autenticacion(view_func):
    """
    Decorador para verificar que el usuario esté autenticado.
    Agrega request.usuario con el usuario autenticado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        usuario = obtener_usuario_desde_token(request)
        if not usuario:
            return Response(
                {'error': 'Token JWT inválido o expirado'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        request.usuario = usuario
        return view_func(request, *args, **kwargs)
    return wrapper

def requiere_rol(*roles_permitidos):
    """
    Decorador para verificar que el usuario tenga uno de los roles permitidos.
    Debe usarse después de @requiere_autenticacion.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'usuario'):
                return Response(
                    {'error': 'Autenticación requerida'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if request.usuario.rol not in roles_permitidos:
                return Response(
                    {'error': 'No tiene permisos para realizar esta acción'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

