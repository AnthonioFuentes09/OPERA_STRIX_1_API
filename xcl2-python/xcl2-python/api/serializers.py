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
    """Serializer para Libro con validaciones"""
    class Meta:
        model = Libro
        fields = ['id', 'titulo', 'autor', 'isbn', 'categoria', 'editorial', 
                  'añoPublicacion', 'copiasDisponibles', 'copiasTotal', 
                  'ubicacion', 'estado', 'descripcion', 'fechaIngreso']
        read_only_fields = ['id', 'fechaIngreso']
    
    def validate(self, data):
        """Valida que copiasDisponibles no exceda copiasTotal y que al reducir copiasTotal no quede menor que copias prestadas"""
        copias_disponibles = data.get('copiasDisponibles', self.instance.copiasDisponibles if self.instance else 0)
        copias_total = data.get('copiasTotal', self.instance.copiasTotal if self.instance else 0)
        
        if copias_disponibles > copias_total:
            raise serializers.ValidationError({
                'copiasDisponibles': 'No puede exceder el total de copias'
            })
        
        # Validar que al reducir copiasTotal no quede menor que la diferencia
        if self.instance:
            copias_prestadas = self.instance.copiasTotal - self.instance.copiasDisponibles
            if copias_total < copias_prestadas:
                raise serializers.ValidationError({
                    'copiasTotal': f'No puede ser menor que {copias_prestadas} (copias actualmente prestadas)'
                })
        
        return data

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
    """Serializer para crear préstamo con validaciones"""
    class Meta:
        model = Prestamo
        fields = ['libro', 'fechaDevolucionEsperada']
    
    def validate_libro(self, value):
        """Valida que el libro tenga copias disponibles"""
        if value.copiasDisponibles <= 0:
            raise serializers.ValidationError('El libro no tiene copias disponibles')
        if value.estado != 'disponible':
            raise serializers.ValidationError('El libro no está disponible para préstamo')
        return value
    
    def validate(self, data):
        """Valida fecha de devolución esperada"""
        from django.utils import timezone
        fecha_devolucion = data.get('fechaDevolucionEsperada')
        if fecha_devolucion and fecha_devolucion <= timezone.now():
            raise serializers.ValidationError({
                'fechaDevolucionEsperada': 'La fecha de devolución debe ser futura'
            })
        return data

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

class ReservaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear reserva con validaciones"""
    class Meta:
        model = Reserva
        fields = ['libro']
    
    def validate_libro(self, value):
        """Valida que el libro esté agotado para permitir reserva"""
        if value.copiasDisponibles > 0:
            raise serializers.ValidationError('El libro tiene copias disponibles. No se requiere reserva.')
        if value.estado == 'en mantenimiento':
            raise serializers.ValidationError('El libro está en mantenimiento y no puede ser reservado')
        return value
