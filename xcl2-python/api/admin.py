from django.contrib import admin
from .models import Usuario, Libro, Prestamo, Reserva

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Usuario"""
    list_display = ['nombre', 'apellido', 'correo', 'rol', 'activo', 'fechaRegistro']
    list_filter = ['rol', 'activo', 'fechaRegistro']
    search_fields = ['nombre', 'apellido', 'correo', 'numeroIdentidad']
    readonly_fields = ['fechaRegistro']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'correo', 'edad', 'numeroIdentidad', 'telefono')
        }),
        ('Seguridad y Acceso', {
            'fields': ('contraseña', 'rol', 'activo')
        }),
        ('Multas', {
            'fields': ('multas',)
        }),
        ('Fechas', {
            'fields': ('fechaRegistro',)
        }),
    )

@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Libro"""
    list_display = ['titulo', 'autor', 'isbn', 'categoria', 'estado', 'copiasDisponibles', 'copiasTotal']
    list_filter = ['categoria', 'estado', 'añoPublicacion']
    search_fields = ['titulo', 'autor', 'isbn', 'editorial']
    readonly_fields = ['fechaIngreso']

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Prestamo"""
    list_display = ['usuario', 'libro', 'fechaPrestamo', 'fechaDevolucionEsperada', 'estado', 'diasRetraso', 'multaGenerada']
    list_filter = ['estado', 'fechaPrestamo']
    search_fields = ['usuario__nombre', 'usuario__apellido', 'libro__titulo']
    readonly_fields = ['fechaPrestamo']

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Reserva"""
    list_display = ['usuario', 'libro', 'fechaReserva', 'estado', 'prioridad', 'fechaNotificacion']
    list_filter = ['estado', 'fechaReserva']
    search_fields = ['usuario__nombre', 'usuario__apellido', 'libro__titulo']
    readonly_fields = ['fechaReserva']
