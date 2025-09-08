#!/usr/bin/env python3
"""
Script de prueba para verificar funcionalidad básica del AIP scraper
"""

import asyncio
import sys
from pathlib import Path
from aip_scraper import AIPScraper, AIpDocument

async def test_basic_scraping():
    """Prueba básica de scraping sin descargar archivos"""
    print("=== Prueba básica de scraping ===")
    
    try:
        scraper = AIPScraper()
        
        # Solo extraer documentos de una sección para prueba
        print("Extrayendo documentos de muestra...")
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto("https://ais.anac.gob.ar/aip")
                await page.wait_for_load_state('networkidle')
                
                # Probar extracción de documentos GEN (sección más pequeña)
                gen_docs = await scraper.scrape_section_documents(page, 'GEN')
                
                print(f"✓ Encontrados {len(gen_docs)} documentos en sección GEN")
                
                # Mostrar primeros 5 documentos
                for i, doc in enumerate(gen_docs[:5]):
                    print(f"  {i+1}. {doc.title}")
                    print(f"     URL: {doc.url}")
                    print(f"     Versión: {doc.version}")
                    print()
                
                # Verificar filtrado de AD
                print("\nProbando filtrado de documentos AD...")
                
                # Simular documentos AD
                test_titles = [
                    "AD-0.6 Indices - Indice",
                    "AD-1.1 AD/HEL Introducción - Disponibilidad",
                    "SAAC-AD-2.0 Aeródromos - Datos del AD CONCORDIA",
                    "SADF-AD-2.0 Aeródromos - Datos del AD SAN FERNANDO",
                    "SABE-AD-2.0 Aeródromos - Datos del AD BUENOS AIRES"
                ]
                
                for title in test_titles:
                    should_include = scraper._should_include_document(title, 'AD')
                    status = "✓ Incluido" if should_include else "✗ Excluido"
                    print(f"  {status}: {title}")
                
                print("\n✅ Prueba básica completada exitosamente")
                return True
                
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"❌ Error en prueba básica: {e}")
        return False

def test_pdf_creation():
    """Prueba creación de PDF básico"""
    print("\n=== Prueba creación de PDF ===")
    
    try:
        from aip_scraper import PDFCombiner, OUTPUT_FOLDER
        
        # Crear documentos de prueba
        test_docs = [
            AIpDocument("GEN-0.1 Prefacio", "http://example.com/1", "GEN", version="02/24"),
            AIpDocument("ENR-1.1 Reglas Generales", "http://example.com/2", "ENR", version="01/25"),
            AIpDocument("AD-0.6 Indices", "http://example.com/3", "AD", version="02/24")
        ]
        
        combiner = PDFCombiner(test_docs)
        
        # Probar agrupación
        sections = combiner._group_documents_by_section()
        print(f"✓ Secciones agrupadas: {list(sections.keys())}")
        
        # Probar creación de índice
        OUTPUT_FOLDER.mkdir(exist_ok=True)
        index_path = combiner.create_index_pdf()
        
        if Path(index_path).exists():
            print(f"✓ Índice creado: {index_path}")
            file_size = Path(index_path).stat().st_size / 1024
            print(f"  Tamaño: {file_size:.1f} KB")
            return True
        else:
            print("❌ Error: No se pudo crear el índice")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de PDF: {e}")
        return False

def test_dependencies():
    """Verifica que todas las dependencias estén disponibles"""
    print("\n=== Verificación de dependencias ===")
    
    dependencies = [
        ('playwright', 'Playwright'),
        ('PyPDF2', 'PyPDF2'),
        ('reportlab', 'ReportLab'),
        ('requests', 'Requests'),
        ('fitz', 'PyMuPDF'),
    ]
    
    missing = []
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"❌ {name} - FALTANTE")
            missing.append(name)
    
    # Dependencias opcionales
    optional_deps = [
        ('pytesseract', 'pytesseract (OCR)'),
        ('PIL', 'Pillow (procesamiento de imágenes)')
    ]
    
    for module, name in optional_deps:
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"⚠ {name} - OPCIONAL")
    
    if missing:
        print(f"\n❌ Dependencias faltantes: {', '.join(missing)}")
        print("Ejecuta: python setup.py")
        return False
    else:
        print("\n✅ Todas las dependencias principales disponibles")
        return True

async def main():
    """Función principal de pruebas"""
    print("AIP Argentina Scraper - Pruebas\n")
    
    tests = [
        ("Dependencias", test_dependencies),
        ("Creación PDF básico", test_pdf_creation),
        ("Scraping básico", test_basic_scraping)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Ejecutando: {test_name}")
        print('='*50)
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
            
        results.append((test_name, result))
    
    # Resumen
    print(f"\n{'='*50}")
    print("RESUMEN DE PRUEBAS")
    print('='*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("\n🎉 ¡Todas las pruebas pasaron! El scraper está listo para usar.")
        print("\nPara ejecutar el scraper completo:")
        print("  python aip_scraper.py")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisar configuración.")
        print("\nPara configurar automáticamente:")
        print("  python setup.py")

if __name__ == "__main__":
    asyncio.run(main())
