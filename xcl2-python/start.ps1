# start.ps1 - shell script para desplegar el backend del proyecto Pokemon API
# Ejecuta: .\start.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pokemon API - Despliegue" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Python está instalado
Write-Host "[1/5] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: Python no está instalado" -ForegroundColor Red
    Write-Host "  Instala Python desde https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Crear/activar entorno virtual
Write-Host ""
Write-Host "[2/5] Configurando entorno virtual..." -ForegroundColor Yellow
$venvPath = "venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "  Creando entorno virtual..." -ForegroundColor Gray
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Error al crear el entorno virtual" -ForegroundColor Red
        exit 1
    }
    Write-Host "Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "Entorno virtual ya existe" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "  Activando entorno virtual..." -ForegroundColor Gray
& "$venvPath\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al activar el entorno virtual" -ForegroundColor Red
    Write-Host "  Intenta ejecutar: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}
Write-Host "Entorno virtual activado" -ForegroundColor Green

# Actualizar pip
Write-Host ""
Write-Host "[3/5] Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "pip actualizado" -ForegroundColor Green

# Instalar dependencias
Write-Host ""
Write-Host "[4/5] Instalando dependencias..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Error al instalar dependencias" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ No se encontró requirements.txt" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencias instaladas" -ForegroundColor Green

# Ejecutar migraciones
Write-Host ""
Write-Host "[5/5] Ejecutando migraciones..." -ForegroundColor Yellow
python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al ejecutar migraciones" -ForegroundColor Red
    exit 1
}
Write-Host "Migraciones completadas" -ForegroundColor Green

# Iniciar servidor
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Servidor iniciando..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API disponible en: http://localhost:8000/api/" -ForegroundColor Green
Write-Host "Endpoints:" -ForegroundColor Green
Write-Host "  - http://localhost:8000/api/generations/" -ForegroundColor Gray
Write-Host "  - http://localhost:8000/api/pokedex/" -ForegroundColor Gray
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host ""

# Iniciar servidor Django
python manage.py runserver

