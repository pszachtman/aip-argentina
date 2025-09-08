#!/bin/bash

# AIP Argentina Scraper - Script de inicio rápido
# Configura automáticamente el entorno y ejecuta el scraper

set -e  # Salir en caso de error

echo "🚁 AIP Argentina Scraper - Inicio Rápido"
echo "========================================"

# Verificar Python
echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "Instala Python 3.8+ desde https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION encontrado"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Configurar Playwright
echo "Configurando Playwright..."
python -m playwright install chromium --quiet

# Verificar configuración con pruebas
echo "Ejecutando pruebas de configuración..."
python test_scraper.py

# Preguntar si continuar
echo ""
read -p "¿Continuar con la descarga completa del AIP? (s/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[SsYy]$ ]]; then
    echo "🚀 Iniciando descarga completa del AIP..."
    echo "Este proceso puede tomar 15-30 minutos..."
    echo ""
    
    # Ejecutar scraper principal
    python aip_scraper.py
    
    echo ""
    echo "🎉 ¡Proceso completado!"
    echo "Archivos generados en: aip_output/"
    echo ""
    echo "Archivos disponibles:"
    ls -lh aip_output/*.pdf 2>/dev/null || echo "No se encontraron PDFs generados"
    
else
    echo "Configuración completada. Para ejecutar manualmente:"
    echo "  source venv/bin/activate"
    echo "  python aip_scraper.py"
fi

echo ""
echo "Logs disponibles en: aip_scraper.log"
