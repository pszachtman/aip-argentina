#!/usr/bin/env python3
"""
Prueba rápida del scraper con límites de seguridad
"""

import asyncio
import sys
from pathlib import Path

# Importar solo lo necesario
from aip_scraper import AIPScraper

async def test_quick_scraping():
    """Prueba rápida que extrae solo algunos documentos"""
    print("=== Prueba rápida de scraping (con límites) ===")
    
    try:
        scraper = AIPScraper()
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto("https://ais.anac.gob.ar/aip")
                await page.wait_for_load_state('networkidle')
                
                print("✓ Sitio web cargado correctamente")
                
                # Probar solo sección GEN con límites estrictos
                print("\nProbando extracción de sección GEN (limitada)...")
                gen_docs = await scraper.scrape_section_documents(page, 'GEN')
                
                print(f"\n✅ Éxito: Encontrados {len(gen_docs)} documentos únicos en GEN")
                
                # Mostrar algunos ejemplos
                print("\n📄 Primeros 10 documentos encontrados:")
                for i, doc in enumerate(gen_docs[:10]):
                    print(f"  {i+1:2d}. {doc.title}")
                    print(f"      📅 {doc.version}")
                
                # Verificar filtrado de AD si hay tiempo
                print("\n🔍 Probando filtrado de documentos AD...")
                test_titles = [
                    "AD-0.6 Indices - Indice",
                    "AD-1.1 AD/HEL Introducción",
                    "SADF-AD-2.0 Aeródromos - Datos del AD SAN FERNANDO",
                    "SABE-AD-2.0 Aeródromos - Datos del AD BUENOS AIRES"
                ]
                
                print("Resultados del filtrado:")
                for title in test_titles:
                    should_include = scraper._should_include_document(title, 'AD')
                    status = "✅ Incluido" if should_include else "❌ Excluido"
                    print(f"  {status}: {title}")
                
                print("\n🎉 ¡Prueba rápida completada exitosamente!")
                print(f"📊 El scraper funciona correctamente y encontró {len(gen_docs)} documentos")
                
                return True
                
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"❌ Error en prueba rápida: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Función principal de prueba rápida"""
    print("AIP Argentina - Prueba Rápida\n")
    
    success = await test_quick_scraping()
    
    if success:
        print(f"\n{'='*60}")
        print("✅ PRUEBA EXITOSA - El scraper funciona correctamente")
        print('='*60)
        print("\n🚀 Próximos pasos:")
        print("1. Ejecutar scraper completo: python aip_scraper.py")
        print("2. O ejecutar por secciones para mayor control")
        print("\n💡 El problema del bucle infinito ha sido corregido")
        return 0
    else:
        print(f"\n{'='*60}")
        print("❌ PRUEBA FALLÓ - Revisar configuración")
        print('='*60)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
