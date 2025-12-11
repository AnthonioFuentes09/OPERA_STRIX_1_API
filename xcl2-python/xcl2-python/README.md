# Sistema de Gestión Bibliotecaria - Backend

Backend Django REST Framework para sistema de gestión bibliotecaria. API REST con autenticación JWT y control de acceso por roles.

## Requisitos

- Python 3.10 o superior
- python3.10-venv (solo Unix/Linux/Mac)

## Inicio Rápido

**Windows:**
```powershell
.\start.ps1
```

**Unix/Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

El script automáticamente configura el entorno virtual, instala dependencias, ejecuta migraciones e inicia el servidor en http://localhost:8000

## Configuración

Crear archivo `.env` en la raíz del proyecto:

```
JWT_SECRET_KEY=tu-clave-secreta-para-jwt-aqui
```

## Documentación de API

Documentación interactiva disponible en:
- **Swagger UI**: http://localhost:8000/api/docs/
- **Schema OpenAPI**: http://localhost:8000/api/schema/

Todos los endpoints están documentados con ejemplos de payloads y respuestas.

## Endpoints Disponibles

### Autenticación
- `POST /api/auth/register` - Registro de nuevo usuario
- `POST /api/auth/login` - Inicio de sesión (retorna JWT)

### Libros
- `POST /api/libros` - Crear libro (bibliotecario/admin)
- `GET /api/libros` - Listar libros (con filtros: categoría, autor, disponibilidad)
- `PUT /api/libros/{id}` - Actualizar libro (bibliotecario/admin)
- `DELETE /api/libros/{id}` - Eliminar libro (bibliotecario/admin)

### Préstamos
- `POST /api/prestamos` - Crear préstamo
- `GET /api/prestamos` - Listar préstamos
- `PUT /api/prestamos/{id}/devolver` - Devolver libro
- `PUT /api/prestamos/{id}/renovar` - Renovar préstamo

### Reservas
- `POST /api/reservas` - Crear reserva
- `GET /api/reservas/mis-reservas` - Mis reservas
- `DELETE /api/reservas/{id}` - Cancelar reserva

### Reportes
- `GET /api/reportes/usuarios-morosos` - Usuarios con multas (bibliotecario/admin)
- `GET /api/reportes/libros-populares` - Top 10 libros más prestados (bibliotecario/admin)
- `GET /api/reportes/mi-historial` - Historial de préstamos del usuario
- `GET /api/prestamos/vencidos` - Préstamos vencidos (bibliotecario/admin)

### Administración
- `PUT /api/usuarios/{id}/cambiar-rol` - Cambiar rol de usuario (admin)
- `PUT /api/usuarios/{id}/gestionar-multa` - Gestionar multas (bibliotecario/admin)
- `PUT /api/usuarios/{id}/toggle-estado` - Activar/desactivar cuenta
- `GET /api/estadisticas` - Dashboard de estadísticas (admin)

## Servicios y Helpers

### Autenticación (`api/auth_helpers.py`)
- `obtener_usuario_desde_token(request)` - Extrae usuario del JWT
- `generar_token_jwt(usuario)` - Genera token JWT con claims
- `@requiere_autenticacion` - Decorador para verificar autenticación
- `@requiere_rol(*roles)` - Decorador para verificar roles

### Modelos (`api/models.py`)
- `Usuario` - Usuarios del sistema (roles: usuario, bibliotecario, admin)
- `Libro` - Catálogo de libros
- `Prestamo` - Registro de préstamos
- `Reserva` - Sistema de reservas

## Autenticación

Los endpoints protegidos requieren el header:
```
Authorization: Bearer {token}
```

El token JWT contiene los claims: `correo`, `rol`, `userId`

## Base de Datos

SQLite - El archivo `db.sqlite3` se crea automáticamente al ejecutar migraciones.
