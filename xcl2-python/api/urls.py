from django.urls import path
from . import views

urlpatterns = [
    # Escenario 1: Autenticación
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    
    # Escenario 2: Libros
    path('libros/', views.listar_libros, name='listar-libros'),
    path('libros/', views.crear_libro, name='crear-libro'),
    path('libros/<int:id>/', views.actualizar_libro, name='actualizar-libro'),
    path('libros/<int:id>/', views.eliminar_libro, name='eliminar-libro'),
    
    # Escenario 3: Préstamos
    path('prestamos/', views.listar_prestamos, name='listar-prestamos'),
    path('prestamos/', views.crear_prestamo, name='crear-prestamo'),
    path('prestamos/<int:id>/devolver/', views.devolver_libro, name='devolver-libro'),
    path('prestamos/<int:id>/renovar/', views.renovar_prestamo, name='renovar-prestamo'),
    
    # Escenario 4: Reservas
    path('reservas/', views.listar_reservas, name='listar-reservas'),
    path('reservas/mis-reservas/', views.listar_reservas, name='mis-reservas'),
    path('reservas/', views.crear_reserva, name='crear-reserva'),
    path('reservas/<int:id>/', views.cancelar_reserva, name='cancelar-reserva'),
    path('reservas/notificar-disponibilidad/', views.notificar_disponibilidad, name='notificar-disponibilidad'),
    
    # Escenario 5: Reportes
    path('reportes/usuarios-morosos/', views.usuarios_morosos, name='usuarios-morosos'),
    path('reportes/libros-populares/', views.libros_populares, name='libros-populares'),
    path('reportes/mi-historial/', views.mi_historial, name='mi-historial'),
    path('prestamos/vencidos/', views.prestamos_vencidos, name='prestamos-vencidos'),
    
    # Escenario 6: Administración
    path('usuarios/<int:id>/cambiar-rol/', views.cambiar_rol_usuario, name='cambiar-rol'),
    path('usuarios/<int:id>/gestionar-multa/', views.gestionar_multa, name='gestionar-multa'),
    path('usuarios/<int:id>/toggle-estado/', views.toggle_estado_usuario, name='toggle-estado'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
]

