#!/bin/bash
# start.sh - Script bash para desplegar el backend del proyecto Pokemon API
# Ejecuta: ./start.sh o bash start.sh

# Colores para output
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Pokemon API - Despliegue${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Detectar sistema operativo y gestor de paquetes
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt-get"
        INSTALL_CMD="sudo apt-get install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        INSTALL_CMD="sudo yum install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        INSTALL_CMD="sudo dnf install -y"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        INSTALL_CMD="sudo pacman -S --noconfirm"
    elif command -v brew &> /dev/null; then
        PKG_MANAGER="brew"
        INSTALL_CMD="brew install"
    else
        PKG_MANAGER="unknown"
        INSTALL_CMD=""
    fi
}

# Verificar e instalar Python si falta
check_and_install_python() {
    echo -e "${YELLOW}[1/5] Verificando Python...${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        echo -e "${YELLOW}  Python no encontrado, intentando instalar...${NC}"
        detect_package_manager
        
        if [ "$PKG_MANAGER" = "apt-get" ]; then
            $INSTALL_CMD python3 python3-pip python3-venv
        elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
            $INSTALL_CMD python3 python3-pip
        elif [ "$PKG_MANAGER" = "pacman" ]; then
            $INSTALL_CMD python python-pip
        elif [ "$PKG_MANAGER" = "brew" ]; then
            $INSTALL_CMD python3
        else
            echo -e "${RED}✗ Error: Python no está instalado y no se pudo detectar el gestor de paquetes${NC}"
            echo -e "${RED}  Instala Python manualmente desde https://www.python.org/${NC}"
            exit 1
        fi
        
        if command -v python3 &> /dev/null; then
            PYTHON_CMD=python3
        elif command -v python &> /dev/null; then
            PYTHON_CMD=python
        else
            echo -e "${RED}✗ Error: No se pudo instalar Python${NC}"
            exit 1
        fi
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo -e "${GREEN}Python encontrado: $PYTHON_VERSION${NC}"
}

# Verificar e instalar python3-venv si falta
check_and_install_venv() {
    if ! $PYTHON_CMD -m venv --help &> /dev/null; then
        echo -e "${YELLOW}  python3-venv no encontrado, intentando instalar...${NC}"
        detect_package_manager
        
        if [ "$PKG_MANAGER" = "apt-get" ]; then
            PYTHON_MINOR=$(echo $PYTHON_VERSION | grep -oP '\d+\.\d+' | head -1)
            $INSTALL_CMD python${PYTHON_MINOR}-venv || $INSTALL_CMD python3-venv
        elif [ "$PKG_MANAGER" = "yum" ] || [ "$PKG_MANAGER" = "dnf" ]; then
            $INSTALL_CMD python3-devel
        elif [ "$PKG_MANAGER" = "pacman" ]; then
            $INSTALL_CMD python
        elif [ "$PKG_MANAGER" = "brew" ]; then
            # brew ya incluye venv con python3
            echo -e "${GRAY}  brew ya incluye venv${NC}"
        fi
        
        if ! $PYTHON_CMD -m venv --help &> /dev/null; then
            echo -e "${RED}✗ Error: No se pudo instalar python3-venv${NC}"
            echo -e "${YELLOW}  Intenta instalarlo manualmente${NC}"
            exit 1
        fi
    fi
}

# Ejecutar verificaciones
check_and_install_python
check_and_install_venv

# Crear/activar entorno virtual
echo ""
echo -e "${YELLOW}[2/5] Configurando entorno virtual...${NC}"
VENV_PATH="venv"

# Eliminar venv si existe y recrearlo
if [ -d "$VENV_PATH" ]; then
    echo -e "${GRAY}  Eliminando entorno virtual existente...${NC}"
    rm -rf $VENV_PATH
fi

echo -e "${GRAY}  Creando entorno virtual...${NC}"
$PYTHON_CMD -m venv $VENV_PATH 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error al crear el entorno virtual${NC}"
    exit 1
fi
echo -e "${GREEN}Entorno virtual creado${NC}"

# Activar entorno virtual
echo -e "${GRAY}  Activando entorno virtual...${NC}"
source "$VENV_PATH/bin/activate"
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error al activar el entorno virtual${NC}"
    exit 1
fi
echo -e "${GREEN}Entorno virtual activado${NC}"

# Actualizar pip
echo ""
echo -e "${YELLOW}[3/5] Actualizando pip...${NC}"
$PYTHON_CMD -m pip install --upgrade pip --quiet
echo -e "${GREEN}pip actualizado${NC}"

# Instalar dependencias
echo ""
echo -e "${YELLOW}[4/5] Instalando dependencias...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Error al instalar dependencias${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ No se encontró requirements.txt${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencias instaladas${NC}"

# Ejecutar migraciones
echo ""
echo -e "${YELLOW}[5/5] Ejecutando migraciones...${NC}"
$PYTHON_CMD manage.py migrate --noinput
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error al ejecutar migraciones${NC}"
    exit 1
fi
echo -e "${GREEN}Migraciones completadas${NC}"

# Iniciar servidor
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Servidor iniciando...${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${GREEN}API disponible en: http://localhost:8000/api/${NC}"
echo -e "${GREEN}Endpoints:${NC}"
echo -e "${GRAY}  - http://localhost:8000/api/generations/${NC}"
echo -e "${GRAY}  - http://localhost:8000/api/pokedex/${NC}"
echo ""
echo -e "${YELLOW}Presiona Ctrl+C para detener el servidor${NC}"
echo ""

# Iniciar servidor Django
$PYTHON_CMD manage.py runserver
