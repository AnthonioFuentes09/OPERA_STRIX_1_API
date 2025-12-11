from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone
from datetime import timedelta
from .auth_helpers import requiere_autenticacion, requiere_rol, generar_token_jwt
from .models import Usuario, Libro, Prestamo, Reserva
from .serializers import (
    UsuarioSerializer, UsuarioCreateSerializer,
    LibroSerializer, PrestamoSerializer, PrestamoCreateSerializer,
    ReservaSerializer, ReservaCreateSerializer
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

# ==================== ESCENARIO 2: GESTIÓN DE LIBROS ====================

@extend_schema(
    summary="Crear nuevo libro",
    description="Agrega un nuevo libro al inventario. Requiere rol 'bibliotecario' o 'admin'. Valida ISBN único y que copiasDisponibles no exceda copiasTotal.",
    parameters=[
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'titulo': {'type': 'string', 'example': 'El Quijote de la Mancha'},
                'autor': {'type': 'string', 'example': 'Miguel de Cervantes'},
                'isbn': {'type': 'string', 'example': '978-84-376-0494-7'},
                'categoria': {'type': 'string', 'example': 'Literatura Clásica'},
                'editorial': {'type': 'string', 'example': 'Editorial Cátedra'},
                'añoPublicacion': {'type': 'integer', 'example': 1605},
                'copiasTotal': {'type': 'integer', 'example': 5},
                'copiasDisponibles': {'type': 'integer', 'example': 5},
                'ubicacion': {'type': 'string', 'example': 'Estante A-3'},
                'descripcion': {'type': 'string', 'example': 'Novela clásica española'},
            },
            'required': ['titulo', 'autor', 'isbn', 'categoria', 'editorial', 'añoPublicacion', 'copiasTotal', 'ubicacion'],
            'example': {
                'titulo': 'El Quijote de la Mancha',
                'autor': 'Miguel de Cervantes',
                'isbn': '978-84-376-0494-7',
                'categoria': 'Literatura Clásica',
                'editorial': 'Editorial Cátedra',
                'añoPublicacion': 1605,
                'copiasTotal': 5,
                'copiasDisponibles': 5,
                'ubicacion': 'Estante A-3',
                'descripcion': 'Novela clásica española del siglo XVII'
            }
        }
    },
    responses={
        201: {
            'description': 'Libro creado exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Libro agregado exitosamente',
                    'libro': {
                        'id': 1,
                        'titulo': 'El Quijote de la Mancha',
                        'autor': 'Miguel de Cervantes',
                        'isbn': '978-84-376-0494-7',
                        'estado': 'disponible'
                    }
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'isbn': ['Este ISBN ya existe'],
                    'copiasDisponibles': ['No puede exceder el total de copias']
                }
            }
        },
        403: {
            'description': 'No autorizado',
            'examples': {
                'application/json': {
                    'error': 'Solo bibliotecarios y administradores pueden crear libros'
                }
            }
        }
    },
    tags=['Libros']
)
@api_view(['POST'])
@requiere_autenticacion
@requiere_rol('bibliotecario', 'admin')
def crear_libro(request):
    """Crea un nuevo libro en el inventario"""
    serializer = LibroSerializer(data=request.data)
    if serializer.is_valid():
        libro = serializer.save()
        return Response({
            'mensaje': 'Libro agregado exitosamente',
            'libro': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Listar libros",
    description="Lista todos los libros con opción de filtrar por categoría, autor o disponibilidad. Requiere autenticación.",
    parameters=[
        OpenApiParameter(
            name='categoria',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filtrar por categoría',
            required=False
        ),
        OpenApiParameter(
            name='autor',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filtrar por autor',
            required=False
        ),
        OpenApiParameter(
            name='disponible',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filtrar por disponibilidad (true para disponibles, false para agotados)',
            required=False
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Lista de libros',
            'examples': {
                'application/json': [
                    {
                        'id': 1,
                        'titulo': 'El Quijote de la Mancha',
                        'autor': 'Miguel de Cervantes',
                        'isbn': '978-84-376-0494-7',
                        'categoria': 'Literatura Clásica',
                        'copiasDisponibles': 3,
                        'copiasTotal': 5,
                        'estado': 'disponible'
                    }
                ]
            }
        }
    },
    tags=['Libros']
)
@api_view(['GET'])
@requiere_autenticacion
def listar_libros(request):
    """Lista libros con filtros opcionales"""
    libros = Libro.objects.all()
    
    # Filtros
    categoria = request.query_params.get('categoria')
    if categoria:
        libros = libros.filter(categoria__icontains=categoria)
    
    autor = request.query_params.get('autor')
    if autor:
        libros = libros.filter(autor__icontains=autor)
    
    disponible = request.query_params.get('disponible')
    if disponible is not None:
        disponible_bool = disponible.lower() == 'true'
        if disponible_bool:
            libros = libros.filter(copiasDisponibles__gt=0, estado='disponible')
        else:
            libros = libros.filter(copiasDisponibles=0)
    
    serializer = LibroSerializer(libros, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    summary="Actualizar libro",
    description="Actualiza información de un libro existente. Requiere rol 'bibliotecario' o 'admin'. Valida que al reducir copiasTotal no quede menor que copias prestadas.",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID del libro',
            required=True
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'titulo': {'type': 'string'},
                'autor': {'type': 'string'},
                'categoria': {'type': 'string'},
                'editorial': {'type': 'string'},
                'añoPublicacion': {'type': 'integer'},
                'copiasTotal': {'type': 'integer'},
                'copiasDisponibles': {'type': 'integer'},
                'ubicacion': {'type': 'string'},
                'estado': {'type': 'string', 'enum': ['disponible', 'agotado', 'en mantenimiento']},
                'descripcion': {'type': 'string'},
            },
            'example': {
                'titulo': 'El Quijote (Edición Actualizada)',
                'copiasTotal': 10,
                'copiasDisponibles': 8
            }
        }
    },
    responses={
        200: {
            'description': 'Libro actualizado exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Libro actualizado exitosamente',
                    'libro': {}
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'copiasTotal': ['No puede ser menor que X (copias actualmente prestadas)']
                }
            }
        },
        404: {
            'description': 'Libro no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Libro no encontrado'
                }
            }
        }
    },
    tags=['Libros']
)
@api_view(['PUT'])
@requiere_autenticacion
@requiere_rol('bibliotecario', 'admin')
def actualizar_libro(request, id):
    """Actualiza un libro existente"""
    try:
        libro = Libro.objects.get(id=id)
    except Libro.DoesNotExist:
        return Response(
            {'error': 'Libro no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = LibroSerializer(libro, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'mensaje': 'Libro actualizado exitosamente',
            'libro': serializer.data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Eliminar libro",
    description="Elimina un libro del inventario. Requiere rol 'bibliotecario' o 'admin'. Valida que no tenga préstamos activos.",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID del libro',
            required=True
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Libro eliminado exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Libro eliminado exitosamente'
                }
            }
        },
        400: {
            'description': 'No se puede eliminar',
            'examples': {
                'application/json': {
                    'error': 'No se puede eliminar un libro con préstamos activos'
                }
            }
        },
        404: {
            'description': 'Libro no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Libro no encontrado'
                }
            }
        }
    },
    tags=['Libros']
)
@api_view(['DELETE'])
@requiere_autenticacion
@requiere_rol('bibliotecario', 'admin')
def eliminar_libro(request, id):
    """Elimina un libro del inventario"""
    try:
        libro = Libro.objects.get(id=id)
    except Libro.DoesNotExist:
        return Response(
            {'error': 'Libro no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar que no tenga préstamos activos
    prestamos_activos = Prestamo.objects.filter(libro=libro, estado='activo').count()
    if prestamos_activos > 0:
        return Response(
            {'error': 'No se puede eliminar un libro con préstamos activos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    libro.delete()
    return Response(
        {'mensaje': 'Libro eliminado exitosamente'},
        status=status.HTTP_200_OK
    )

# ==================== ESCENARIO 3: GESTIÓN DE PRÉSTAMOS ====================

@extend_schema(
    summary="Crear préstamo",
    description="Crea un nuevo préstamo de libro. Valida que el libro tenga copias disponibles, que el usuario no tenga multas pendientes y reduce las copias disponibles del libro.",
    parameters=[
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'libro': {'type': 'integer', 'example': 1},
                'fechaDevolucionEsperada': {'type': 'string', 'format': 'date-time', 'example': '2024-12-31T23:59:59Z'},
            },
            'required': ['libro', 'fechaDevolucionEsperada'],
            'example': {
                'libro': 1,
                'fechaDevolucionEsperada': '2024-12-31T23:59:59Z'
            }
        }
    },
    responses={
        201: {
            'description': 'Préstamo creado exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Préstamo creado exitosamente',
                    'prestamo': {
                        'id': 1,
                        'usuario': 1,
                        'libro': 1,
                        'fechaPrestamo': '2024-01-15T10:00:00Z',
                        'fechaDevolucionEsperada': '2024-12-31T23:59:59Z',
                        'estado': 'activo'
                    }
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'libro': ['El libro no tiene copias disponibles'],
                    'error': 'El usuario tiene multas pendientes'
                }
            }
        }
    },
    tags=['Préstamos']
)
@api_view(['POST'])
@requiere_autenticacion
def crear_prestamo(request):
    """Crea un nuevo préstamo de libro"""
    usuario = request.usuario
    
    # Validar que el usuario no tenga multas pendientes
    if usuario.multas > 0:
        return Response(
            {'error': 'El usuario tiene multas pendientes. Debe pagarlas antes de solicitar préstamos.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar que el usuario esté activo
    if not usuario.activo:
        return Response(
            {'error': 'Usuario inactivo. Contacte al administrador.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = PrestamoCreateSerializer(data=request.data)
    if serializer.is_valid():
        libro = serializer.validated_data['libro']
        
        # Reducir copias disponibles
        libro.copiasDisponibles -= 1
        libro.save()
        
        # Crear préstamo
        prestamo = Prestamo.objects.create(
            usuario=usuario,
            libro=libro,
            fechaDevolucionEsperada=serializer.validated_data['fechaDevolucionEsperada'],
            estado='activo',
            renovaciones=0
        )
        
        prestamo_data = PrestamoSerializer(prestamo).data
        return Response({
            'mensaje': 'Préstamo creado exitosamente',
            'prestamo': prestamo_data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Listar préstamos",
    description="Lista préstamos con filtros opcionales. Los usuarios solo ven sus propios préstamos, bibliotecarios y admins ven todos.",
    parameters=[
        OpenApiParameter(
            name='usuario',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filtrar por ID de usuario (solo bibliotecario/admin)',
            required=False
        ),
        OpenApiParameter(
            name='libro',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filtrar por ID de libro',
            required=False
        ),
        OpenApiParameter(
            name='estado',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filtrar por estado: activo, devuelto, vencido',
            required=False
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Lista de préstamos',
            'examples': {
                'application/json': [
                    {
                        'id': 1,
                        'usuario': 1,
                        'usuario_nombre': 'Juan Pérez',
                        'libro': 1,
                        'libro_titulo': 'El Quijote',
                        'estado': 'activo',
                        'fechaPrestamo': '2024-01-15T10:00:00Z',
                        'fechaDevolucionEsperada': '2024-12-31T23:59:59Z'
                    }
                ]
            }
        }
    },
    tags=['Préstamos']
)
@api_view(['GET'])
@requiere_autenticacion
def listar_prestamos(request):
    """Lista préstamos con filtros opcionales"""
    usuario = request.usuario
    
    # Usuarios normales solo ven sus préstamos
    if usuario.rol == 'usuario':
        prestamos = Prestamo.objects.filter(usuario=usuario)
    else:
        # Bibliotecarios y admins ven todos
        prestamos = Prestamo.objects.all()
    
    # Filtros
    usuario_id = request.query_params.get('usuario')
    if usuario_id and usuario.rol in ['bibliotecario', 'admin']:
        prestamos = prestamos.filter(usuario_id=usuario_id)
    
    libro_id = request.query_params.get('libro')
    if libro_id:
        prestamos = prestamos.filter(libro_id=libro_id)
    
    estado = request.query_params.get('estado')
    if estado:
        prestamos = prestamos.filter(estado=estado)
    
    serializer = PrestamoSerializer(prestamos, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    summary="Devolver libro",
    description="Registra la devolución de un libro. Calcula multas por retraso, actualiza estado del préstamo y aumenta copias disponibles del libro.",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID del préstamo',
            required=True
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Libro devuelto exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Libro devuelto exitosamente',
                    'prestamo': {
                        'id': 1,
                        'estado': 'devuelto',
                        'fechaDevolucionReal': '2024-01-20T10:00:00Z',
                        'diasRetraso': 0,
                        'multaGenerada': 0.00
                    }
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'error': 'El préstamo ya fue devuelto'
                }
            }
        },
        403: {
            'description': 'No autorizado',
            'examples': {
                'application/json': {
                    'error': 'Solo puedes devolver tus propios préstamos'
                }
            }
        },
        404: {
            'description': 'Préstamo no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Préstamo no encontrado'
                }
            }
        }
    },
    tags=['Préstamos']
)
@api_view(['PUT'])
@requiere_autenticacion
def devolver_libro(request, id):
    """Registra la devolución de un libro"""
    try:
        prestamo = Prestamo.objects.get(id=id)
    except Prestamo.DoesNotExist:
        return Response(
            {'error': 'Préstamo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar permisos: usuarios solo pueden devolver sus propios préstamos
    if request.usuario.rol == 'usuario' and prestamo.usuario != request.usuario:
        return Response(
            {'error': 'Solo puedes devolver tus propios préstamos'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validar que el préstamo esté activo
    if prestamo.estado != 'activo':
        return Response(
            {'error': 'El préstamo ya fue devuelto'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calcular días de retraso y multa
    fecha_actual = timezone.now()
    fecha_esperada = prestamo.fechaDevolucionEsperada
    
    dias_retraso = 0
    multa = 0.00
    
    if fecha_actual > fecha_esperada:
        dias_retraso = (fecha_actual - fecha_esperada).days
        # Multa: 10 Lempiras por día de retraso
        multa = dias_retraso * 10.00
    
    # Actualizar préstamo
    prestamo.fechaDevolucionReal = fecha_actual
    prestamo.diasRetraso = dias_retraso
    prestamo.multaGenerada = multa
    prestamo.estado = 'devuelto'
    prestamo.save()
    
    # Actualizar multas del usuario
    if multa > 0:
        prestamo.usuario.multas += multa
        prestamo.usuario.save()
    
    # Aumentar copias disponibles del libro
    libro = prestamo.libro
    libro.copiasDisponibles += 1
    libro.save()
    
    prestamo_data = PrestamoSerializer(prestamo).data
    return Response({
        'mensaje': 'Libro devuelto exitosamente',
        'prestamo': prestamo_data
    }, status=status.HTTP_200_OK)

@extend_schema(
    summary="Renovar préstamo",
    description="Renueva un préstamo activo. Valida que no exceda el límite de renovaciones (máximo 2) y actualiza la fecha de devolución esperada.",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID del préstamo',
            required=True
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'fechaDevolucionEsperada': {'type': 'string', 'format': 'date-time', 'example': '2025-01-31T23:59:59Z'},
            },
            'required': ['fechaDevolucionEsperada'],
            'example': {
                'fechaDevolucionEsperada': '2025-01-31T23:59:59Z'
            }
        }
    },
    responses={
        200: {
            'description': 'Préstamo renovado exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Préstamo renovado exitosamente',
                    'prestamo': {
                        'id': 1,
                        'renovaciones': 1,
                        'fechaDevolucionEsperada': '2025-01-31T23:59:59Z'
                    }
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'error': 'El préstamo ha alcanzado el límite de renovaciones (2)',
                    'fechaDevolucionEsperada': ['La fecha de devolución debe ser futura']
                }
            }
        },
        403: {
            'description': 'No autorizado',
            'examples': {
                'application/json': {
                    'error': 'Solo puedes renovar tus propios préstamos'
                }
            }
        },
        404: {
            'description': 'Préstamo no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Préstamo no encontrado'
                }
            }
        }
    },
    tags=['Préstamos']
)
@api_view(['PUT'])
@requiere_autenticacion
def renovar_prestamo(request, id):
    """Renueva un préstamo activo"""
    try:
        prestamo = Prestamo.objects.get(id=id)
    except Prestamo.DoesNotExist:
        return Response(
            {'error': 'Préstamo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar permisos: usuarios solo pueden renovar sus propios préstamos
    if request.usuario.rol == 'usuario' and prestamo.usuario != request.usuario:
        return Response(
            {'error': 'Solo puedes renovar tus propios préstamos'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validar que el préstamo esté activo
    if prestamo.estado != 'activo':
        return Response(
            {'error': 'Solo se pueden renovar préstamos activos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar límite de renovaciones (máximo 2)
    if prestamo.renovaciones >= 2:
        return Response(
            {'error': 'El préstamo ha alcanzado el límite de renovaciones (2)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar fecha de devolución
    nueva_fecha = request.data.get('fechaDevolucionEsperada')
    if not nueva_fecha:
        return Response(
            {'error': 'fechaDevolucionEsperada es requerida'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from django.utils.dateparse import parse_datetime
        fecha_devolucion = parse_datetime(nueva_fecha)
        if fecha_devolucion <= timezone.now():
            return Response(
                {'error': 'La fecha de devolución debe ser futura'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except (ValueError, TypeError):
        return Response(
            {'error': 'Formato de fecha inválido. Use formato ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Actualizar préstamo
    prestamo.fechaDevolucionEsperada = fecha_devolucion
    prestamo.renovaciones += 1
    prestamo.save()
    
    prestamo_data = PrestamoSerializer(prestamo).data
    return Response({
        'mensaje': 'Préstamo renovado exitosamente',
        'prestamo': prestamo_data
    }, status=status.HTTP_200_OK)

# ==================== ESCENARIO 4: SISTEMA DE RESERVAS ====================

@extend_schema(
    summary="Crear reserva",
    description="Crea una reserva para un libro agotado. Asigna prioridad automáticamente según el orden de reserva. Valida que el libro esté agotado y que el usuario no tenga multas pendientes.",
    parameters=[
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'libro': {'type': 'integer', 'example': 1},
            },
            'required': ['libro'],
            'example': {
                'libro': 1
            }
        }
    },
    responses={
        201: {
            'description': 'Reserva creada exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Reserva creada exitosamente',
                    'reserva': {
                        'id': 1,
                        'usuario': 1,
                        'libro': 1,
                        'estado': 'pendiente',
                        'prioridad': 1,
                        'fechaReserva': '2024-01-15T10:00:00Z'
                    }
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'libro': ['El libro tiene copias disponibles. No se requiere reserva.'],
                    'error': 'El usuario tiene multas pendientes'
                }
            }
        }
    },
    tags=['Reservas']
)
@api_view(['POST'])
@requiere_autenticacion
def crear_reserva(request):
    """Crea una nueva reserva de libro"""
    usuario = request.usuario
    
    # Validar que el usuario no tenga multas pendientes
    if usuario.multas > 0:
        return Response(
            {'error': 'El usuario tiene multas pendientes. Debe pagarlas antes de hacer reservas.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar que el usuario esté activo
    if not usuario.activo:
        return Response(
            {'error': 'Usuario inactivo. Contacte al administrador.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validar que el usuario no tenga ya una reserva activa para este libro
    reserva_existente = Reserva.objects.filter(
        usuario=usuario,
        libro_id=request.data.get('libro'),
        estado__in=['pendiente', 'notificada']
    ).exists()
    
    if reserva_existente:
        return Response(
            {'error': 'Ya tienes una reserva activa para este libro'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = ReservaCreateSerializer(data=request.data)
    if serializer.is_valid():
        libro = serializer.validated_data['libro']
        
        # Calcular prioridad: contar reservas pendientes/notificadas para este libro
        reservas_activas = Reserva.objects.filter(
            libro=libro,
            estado__in=['pendiente', 'notificada']
        ).count()
        
        prioridad = reservas_activas + 1
        
        # Crear reserva
        reserva = Reserva.objects.create(
            usuario=usuario,
            libro=libro,
            estado='pendiente',
            prioridad=prioridad
        )
        
        reserva_data = ReservaSerializer(reserva).data
        return Response({
            'mensaje': 'Reserva creada exitosamente',
            'reserva': reserva_data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Listar reservas",
    description="Lista las reservas del usuario autenticado. Los usuarios solo ven sus propias reservas, bibliotecarios y admins pueden ver todas con filtros.",
    parameters=[
        OpenApiParameter(
            name='estado',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filtrar por estado: pendiente, notificada, completada, cancelada',
            required=False
        ),
        OpenApiParameter(
            name='libro',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filtrar por ID de libro (solo bibliotecario/admin)',
            required=False
        ),
        OpenApiParameter(
            name='usuario',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filtrar por ID de usuario (solo bibliotecario/admin)',
            required=False
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Lista de reservas',
            'examples': {
                'application/json': [
                    {
                        'id': 1,
                        'usuario': 1,
                        'usuario_nombre': 'Juan Pérez',
                        'libro': 1,
                        'libro_titulo': 'El Quijote',
                        'estado': 'pendiente',
                        'prioridad': 1,
                        'fechaReserva': '2024-01-15T10:00:00Z'
                    }
                ]
            }
        }
    },
    tags=['Reservas']
)
@api_view(['GET'])
@requiere_autenticacion
def listar_reservas(request):
    """Lista reservas del usuario o todas si es bibliotecario/admin"""
    usuario = request.usuario
    
    # Usuarios normales solo ven sus reservas
    if usuario.rol == 'usuario':
        reservas = Reserva.objects.filter(usuario=usuario)
    else:
        # Bibliotecarios y admins ven todas
        reservas = Reserva.objects.all()
    
    # Filtros
    estado = request.query_params.get('estado')
    if estado:
        reservas = reservas.filter(estado=estado)
    
    libro_id = request.query_params.get('libro')
    if libro_id and usuario.rol in ['bibliotecario', 'admin']:
        reservas = reservas.filter(libro_id=libro_id)
    
    usuario_id = request.query_params.get('usuario')
    if usuario_id and usuario.rol in ['bibliotecario', 'admin']:
        reservas = reservas.filter(usuario_id=usuario_id)
    
    serializer = ReservaSerializer(reservas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    summary="Cancelar reserva",
    description="Cancela una reserva. Solo se pueden cancelar reservas en estado 'pendiente' o 'notificada'. Los usuarios solo pueden cancelar sus propias reservas.",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='ID de la reserva',
            required=True
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Reserva cancelada exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Reserva cancelada exitosamente'
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'error': 'Solo se pueden cancelar reservas pendientes o notificadas'
                }
            }
        },
        403: {
            'description': 'No autorizado',
            'examples': {
                'application/json': {
                    'error': 'Solo puedes cancelar tus propias reservas'
                }
            }
        },
        404: {
            'description': 'Reserva no encontrada',
            'examples': {
                'application/json': {
                    'error': 'Reserva no encontrada'
                }
            }
        }
    },
    tags=['Reservas']
)
@api_view(['DELETE'])
@requiere_autenticacion
def cancelar_reserva(request, id):
    """Cancela una reserva"""
    try:
        reserva = Reserva.objects.get(id=id)
    except Reserva.DoesNotExist:
        return Response(
            {'error': 'Reserva no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar permisos: usuarios solo pueden cancelar sus propias reservas
    if request.usuario.rol == 'usuario' and reserva.usuario != request.usuario:
        return Response(
            {'error': 'Solo puedes cancelar tus propias reservas'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validar que la reserva pueda ser cancelada
    if reserva.estado not in ['pendiente', 'notificada']:
        return Response(
            {'error': 'Solo se pueden cancelar reservas pendientes o notificadas'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Actualizar estado y recalcular prioridades
    reserva.estado = 'cancelada'
    reserva.save()
    
    # Recalcular prioridades de las reservas restantes para este libro
    reservas_activas = Reserva.objects.filter(
        libro=reserva.libro,
        estado__in=['pendiente', 'notificada']
    ).order_by('fechaReserva')
    
    for index, reserva_activa in enumerate(reservas_activas, start=1):
        reserva_activa.prioridad = index
        reserva_activa.save()
    
    return Response(
        {'mensaje': 'Reserva cancelada exitosamente'},
        status=status.HTTP_200_OK
    )

@extend_schema(
    summary="Notificar disponibilidad de libro",
    description="Notifica a los usuarios en lista de espera cuando un libro está disponible. Solo bibliotecarios y admins pueden ejecutar esta acción. Actualiza el estado de la reserva con mayor prioridad a 'notificada'.",
    parameters=[
        OpenApiParameter(
            name='libro',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='ID del libro',
            required=True
        ),
        OpenApiParameter(
            name='Authorization',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.HEADER,
            description='Token JWT: Bearer {token}',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Notificación enviada exitosamente',
            'examples': {
                'application/json': {
                    'mensaje': 'Usuario notificado exitosamente',
                    'reserva': {
                        'id': 1,
                        'usuario': 1,
                        'libro': 1,
                        'estado': 'notificada',
                        'fechaNotificacion': '2024-01-20T10:00:00Z'
                    }
                }
            }
        },
        400: {
            'description': 'Error de validación',
            'examples': {
                'application/json': {
                    'error': 'El libro no tiene copias disponibles',
                    'error': 'No hay reservas pendientes para este libro'
                }
            }
        },
        404: {
            'description': 'Libro no encontrado',
            'examples': {
                'application/json': {
                    'error': 'Libro no encontrado'
                }
            }
        }
    },
    tags=['Reservas']
)
@api_view(['PUT'])
@requiere_autenticacion
@requiere_rol('bibliotecario', 'admin')
def notificar_disponibilidad(request):
    """Notifica a usuarios en lista de espera cuando un libro está disponible"""
    libro_id = request.query_params.get('libro')
    
    if not libro_id:
        return Response(
            {'error': 'Parámetro "libro" es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        libro = Libro.objects.get(id=libro_id)
    except Libro.DoesNotExist:
        return Response(
            {'error': 'Libro no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar que el libro tenga copias disponibles
    if libro.copiasDisponibles <= 0:
        return Response(
            {'error': 'El libro no tiene copias disponibles'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Buscar la reserva con mayor prioridad (menor número de prioridad)
    reserva_pendiente = Reserva.objects.filter(
        libro=libro,
        estado='pendiente'
    ).order_by('prioridad', 'fechaReserva').first()
    
    if not reserva_pendiente:
        return Response(
            {'error': 'No hay reservas pendientes para este libro'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Actualizar reserva a notificada
    reserva_pendiente.estado = 'notificada'
    reserva_pendiente.fechaNotificacion = timezone.now()
    # Establecer fecha de expiración: 3 días desde la notificación
    reserva_pendiente.fechaExpiracion = timezone.now() + timedelta(days=3)
    reserva_pendiente.save()
    
    reserva_data = ReservaSerializer(reserva_pendiente).data
    return Response({
        'mensaje': 'Usuario notificado exitosamente',
        'reserva': reserva_data
    }, status=status.HTTP_200_OK)

# Los demás escenarios se implementarán aquí
