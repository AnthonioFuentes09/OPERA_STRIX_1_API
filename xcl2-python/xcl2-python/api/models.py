from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Usuario(models.Model):
    """Modelo de usuario del sistema bibliotecario"""
    ROLES = [
        ('usuario', 'Usuario'),
        ('bibliotecario', 'Bibliotecario'),
        ('admin', 'Administrador'),
    ]
    
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    correo = models.EmailField(unique=True, verbose_name="Correo Electrónico")
    contraseña = models.CharField(max_length=128, verbose_name="Contraseña")
    edad = models.IntegerField(verbose_name="Edad")
    numeroIdentidad = models.CharField(max_length=50, unique=True, verbose_name="Número de Identidad")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario', verbose_name="Rol")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fechaRegistro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    multas = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Multas (Lempiras)")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.correo})"

    def set_password(self, raw_password):
        """Encripta y almacena la contraseña"""
        self.contraseña = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        """Verifica si la contraseña es correcta"""
        return check_password(raw_password, self.contraseña)

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.nombre} {self.apellido}"


class Libro(models.Model):
    """Modelo de libro del catálogo bibliotecario"""
    ESTADOS = [
        ('disponible', 'Disponible'),
        ('agotado', 'Agotado'),
        ('en mantenimiento', 'En Mantenimiento'),
    ]
    
    titulo = models.CharField(max_length=200, verbose_name="Título")
    autor = models.CharField(max_length=100, verbose_name="Autor")
    isbn = models.CharField(max_length=20, unique=True, verbose_name="ISBN")
    categoria = models.CharField(max_length=100, verbose_name="Categoría")
    editorial = models.CharField(max_length=100, verbose_name="Editorial")
    añoPublicacion = models.IntegerField(verbose_name="Año de Publicación")
    copiasDisponibles = models.IntegerField(default=0, verbose_name="Copias Disponibles")
    copiasTotal = models.IntegerField(default=0, verbose_name="Copias Total")
    ubicacion = models.CharField(max_length=100, verbose_name="Ubicación")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='disponible', verbose_name="Estado")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    fechaIngreso = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Ingreso")

    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ['titulo']

    def __str__(self):
        return f"{self.titulo} - {self.autor}"

    def save(self, *args, **kwargs):
        """Actualiza el estado según las copias disponibles"""
        if self.copiasDisponibles == 0:
            self.estado = 'agotado'
        elif self.copiasDisponibles > 0 and self.estado == 'agotado':
            self.estado = 'disponible'
        super().save(*args, **kwargs)


class Prestamo(models.Model):
    """Modelo de préstamo de libros"""
    ESTADOS = [
        ('activo', 'Activo'),
        ('devuelto', 'Devuelto'),
        ('vencido', 'Vencido'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='prestamos', verbose_name="Usuario")
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name='prestamos', verbose_name="Libro")
    fechaPrestamo = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Préstamo")
    fechaDevolucionEsperada = models.DateTimeField(verbose_name="Fecha de Devolución Esperada")
    fechaDevolucionReal = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Devolución Real")
    diasRetraso = models.IntegerField(default=0, verbose_name="Días de Retraso")
    multaGenerada = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Multa Generada (Lempiras)")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='activo', verbose_name="Estado")
    renovaciones = models.IntegerField(default=0, verbose_name="Renovaciones")

    class Meta:
        verbose_name = "Préstamo"
        verbose_name_plural = "Préstamos"
        ordering = ['-fechaPrestamo']

    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.libro.titulo} ({self.estado})"


class Reserva(models.Model):
    """Modelo de reserva de libros"""
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('notificada', 'Notificada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reservas', verbose_name="Usuario")
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name='reservas', verbose_name="Libro")
    fechaReserva = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Reserva")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente', verbose_name="Estado")
    fechaNotificacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Notificación")
    fechaExpiracion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Expiración")
    prioridad = models.IntegerField(default=1, verbose_name="Prioridad")

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['prioridad', 'fechaReserva']

    def __str__(self):
        return f"{self.usuario.nombre_completo} - {self.libro.titulo} ({self.estado})"
