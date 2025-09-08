#!/usr/bin/env python3
"""
Script de configuración inicial para AIP Argentina Scraper
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    """Ejecuta un comando y muestra el resultado"""
    print(f"Ejecutando: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Se requiere Python 3.8 o superior")
        print(f"Versión actual: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} OK")
    return True

def install_requirements():
    """Instala las dependencias de Python"""
    print("\n=== Instalando dependencias de Python ===")
    return run_command(f"{sys.executable} -m pip install -r requirements.txt")

def setup_playwright():
    """Configura Playwright y descarga browsers"""
    print("\n=== Configurando Playwright ===")
    if not run_command(f"{sys.executable} -m playwright install chromium"):
        print("Error instalando browsers de Playwright")
        return False
    return True

def check_tesseract():
    """Verifica si Tesseract está instalado (opcional para OCR)"""
    print("\n=== Verificando Tesseract (OCR) ===")
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Tesseract encontrado")
            print("Para mejor OCR en español, instala el paquete de idioma:")
            print("  macOS: brew install tesseract-lang")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠ Tesseract no encontrado (opcional)")
    print("Para habilitar OCR completo, instala Tesseract:")
    print("  macOS: brew install tesseract")
    print("  Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-spa")
    print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
    return False

def create_directories():
    """Crea directorios necesarios"""
    print("\n=== Creando directorios ===")
    dirs = ['aip_downloads', 'aip_output', 'temp_aip']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ Directorio creado: {dir_name}")

def main():
    """Configuración principal"""
    print("=== AIP Argentina Scraper - Configuración Inicial ===\n")
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_requirements():
        print("Error instalando dependencias")
        sys.exit(1)
    
    # Configurar Playwright
    if not setup_playwright():
        print("Error configurando Playwright")
        sys.exit(1)
    
    # Verificar Tesseract (opcional)
    check_tesseract()
    
    # Crear directorios
    create_directories()
    
    print("\n=== ✓ Configuración completada ===")
    print("\nPara ejecutar el scraper:")
    print("  python aip_scraper.py")
    print("\nPara más información, consulta README.md")

if __name__ == "__main__":
    main()
