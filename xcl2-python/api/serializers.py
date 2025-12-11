from rest_framework import serializers
from .models import Usuario, Libro, Prestamo, Reserva

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para lectura de Usuario"""
    nombre_completo = serializers.CharField(source='nombre_completo', read_only=True)
    
    class Meta:
        model = Usuario
        fields = ['id', 'nombre', 'apellido', 'nombre_completo', 'correo', 'edad', 
                  'numeroIdentidad', 'telefono', 'rol', 'activo', 'fechaRegistro', 'multas']
        read_only_fields = ['id', 'fechaRegistro']

class UsuarioCreateSerializer(serializers.ModelSerializer):
    """Serializer para registro de nuevo usuario"""
    contraseña = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'contraseña', 'edad', 
                  'numeroIdentidad', 'telefono']
    
    def create(self, validated_data):
        """Crea usuario con contraseña hasheada y valores por defecto"""
        contraseña = validated_data.pop('contraseña')
        usuario = Usuario.objects.create(
            **validated_data,
            rol='usuario',
            activo=True,
            multas=0.00
        )
        usuario.set_password(contraseña)
        return usuario

class LibroSerializer(serializers.ModelSerializer):
    """Serializer para Libro"""
    class Meta:
        model = Libro
        fields = ['id', 'titulo', 'autor', 'isbn', 'categoria', 'editorial', 
                  'añoPublicacion', 'copiasDisponibles', 'copiasTotal', 
                  'ubicacion', 'estado', 'descripcion', 'fechaIngreso']
        read_only_fields = ['id', 'fechaIngreso']

class PrestamoSerializer(serializers.ModelSerializer):
    """Serializer para Prestamo con información relacionada"""
    usuario_nombre = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    libro_titulo = serializers.CharField(source='libro.titulo', read_only=True)
    libro_autor = serializers.CharField(source='libro.autor', read_only=True)
    
    class Meta:
        model = Prestamo
        fields = ['id', 'usuario', 'usuario_nombre', 'libro', 'libro_titulo', 
                  'libro_autor', 'fechaPrestamo', 'fechaDevolucionEsperada', 
                  'fechaDevolucionReal', 'diasRetraso', 'multaGenerada', 
                  'estado', 'renovaciones']
        read_only_fields = ['id', 'fechaPrestamo', 'diasRetraso', 'multaGenerada']

class PrestamoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear préstamo"""
    class Meta:
        model = Prestamo
        fields = ['libro', 'fechaDevolucionEsperada']

class ReservaSerializer(serializers.ModelSerializer):
    """Serializer para Reserva con información relacionada"""
    usuario_nombre = serializers.CharField(source='usuario.nombre_completo', read_only=True)
    libro_titulo = serializers.CharField(source='libro.titulo', read_only=True)
    libro_autor = serializers.CharField(source='libro.autor', read_only=True)
    
    class Meta:
        model = Reserva
        fields = ['id', 'usuario', 'usuario_nombre', 'libro', 'libro_titulo', 
                  'libro_autor', 'fechaReserva', 'estado', 'fechaNotificacion', 
                  'fechaExpiracion', 'prioridad']
        read_only_fields = ['id', 'fechaReserva', 'prioridad']
