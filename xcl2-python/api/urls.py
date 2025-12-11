from django.urls import path
from . import views

urlpatterns = [
    # Escenario 1: Autenticación
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    
    # Los demás endpoints se agregarán aquí según los escenarios
]

