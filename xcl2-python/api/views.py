from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .auth_helpers import requiere_autenticacion, requiere_rol, generar_token_jwt
from .models import Usuario, Libro, Prestamo, Reserva
from .serializers import (
    UsuarioSerializer, UsuarioCreateSerializer,
    LibroSerializer, PrestamoSerializer, PrestamoCreateSerializer,
    ReservaSerializer
)

# ==================== ESCENARIO 1: AUTENTICACIÓN ====================

@extend_schema(
    summary="Registro de nuevo usuario",
    description="Crea un nuevo usuario en el sistema. El rol se asigna automáticamente como 'usuario', multas en 0 y activo en true.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'nombre': {'type': 'string', 'example': 'Juan'},
                'apellido': {'type': 'string', 'example': 'Pérez'},
                'correo': {'type': 'string', 'format': 'email', 'example': 'juan.perez@email.com'},
                'contraseña': {'type': 'string', 'example': 'password123'},
                'edad': {'type': 'integer', 'example': 25},
                'numeroIdentidad': {'type': 'string', 'example': '0801-1990-12345'},
                'telefono': {'type': 'string', 'example': '+504 9876-5432'},
            },
            'required': ['nombre', 'apellido', 'correo', 'contraseña', 'edad', 'numeroIdentidad', 'telefono'],
            'example': {
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'correo': 'juan.perez@email.com',
                'contraseña': 'password123',
                'edad': 25,
                'numeroIdentidad': '0801-1990-12345',
                'telefono': '+504 9876-5432'
            }
        }
    },
    responses={
        201: {
            'description': 'Usuario creado exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Usuario registrado exitosamente',
                    'usuario': {
                        'id': 1,
                        'nombre': 'Juan',
                        'apellido': 'Pérez',
                        'correo': 'juan.perez@email.com',
                        'rol': 'usuario',
                        'activo': True,
                        'multas': 0.00
                    }
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'correo': ['Este correo ya está registrado'],
                    'numeroIdentidad': ['Este número de identidad ya existe']
                }
            }
        }
    },
    tags=['Autenticación']
)
@api_view(['POST'])
def register(request):
    """
    Endpoint de registro de nuevos usuarios.
    Valida que el correo sea único, hashea la contraseña, asigna rol 'usuario' por defecto.
    """
    serializer = UsuarioCreateSerializer(data=request.data)
    if serializer.is_valid():
        usuario = serializer.save()
        usuario_data = UsuarioSerializer(usuario).data
        return Response({
            'mensaje': 'Usuario registrado exitosamente',
            'usuario': usuario_data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Inicio de sesión",
    description="Autentica un usuario y retorna un token JWT con claims de correo, rol y userId. Verifica que la cuenta esté activa.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'correo': {'type': 'string', 'format': 'email', 'example': 'juan.perez@email.com'},
                'contraseña': {'type': 'string', 'example': 'password123'},
            },
            'required': ['correo', 'contraseña'],
            'example': {
                'correo': 'juan.perez@email.com',
                'contraseña': 'password123'
            }
        }
    },
    responses={
        200: {
            'description': 'Login exitoso',
            'examples': {
                'application/json': {
                    'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                    'usuario': {
                        'id': 1,
                        'nombre': 'Juan',
                        'apellido': 'Pérez',
                        'correo': 'juan.perez@email.com',
                        'rol': 'usuario'
                    }
                }
            }
        },
        400: {
            'description': 'Campos faltantes',
            'examples': {
                'application/json': {
                    'error': 'Correo y contraseña son requeridos'
                }
            }
        },
        401: {
            'description': 'Credenciales inválidas',
            'examples': {
                'application/json': {
                    'error': 'Correo o contraseña incorrectos'
                }
            }
        },
        403: {
            'description': 'Cuenta inactiva',
            'examples': {
                'application/json': {
                    'error': 'Cuenta inactiva. Contacte al administrador.'
                }
            }
        }
    },
    tags=['Autenticación']
)
@api_view(['POST'])
def login(request):
    """
    Endpoint de inicio de sesión.
    Valida credenciales, verifica cuenta activa y genera token JWT.
    """
    correo = request.data.get('correo')
    contraseña = request.data.get('contraseña')
    
    if not correo or not contraseña:
        return Response(
            {'error': 'Correo y contraseña son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        usuario = Usuario.objects.get(correo=correo)
    except Usuario.DoesNotExist:
        return Response(
            {'error': 'Correo o contraseña incorrectos'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not usuario.activo:
        return Response(
            {'error': 'Cuenta inactiva. Contacte al administrador.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if not usuario.check_password(contraseña):
        return Response(
            {'error': 'Correo o contraseña incorrectos'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token = generar_token_jwt(usuario)
    usuario_data = UsuarioSerializer(usuario).data
    
    return Response({
        'token': token,
        'usuario': usuario_data
    }, status=status.HTTP_200_OK)

# Los demás escenarios se implementarán aquí
