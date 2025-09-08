#!/usr/bin/env python3
"""
Optimizador para crear una versión reducida del PDF GEN
Excluye SOLO documentos administrativos (registros de enmiendas, etc.)
Mantiene tasas/derechos y tablas de sol según pedido del usuario
"""

import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
import os

def create_optimized_gen():
    """Crea una versión optimizada del PDF GEN excluyendo documentos menos críticos"""
    
    # Documentos a EXCLUIR para reducir tamaño (solo administrativos)
    exclude_patterns = [
        "GEN-02",  # Registro de Enmiendas (administrativo)
        "GEN-03",  # Registro de Suplementos (administrativo)  
        "GEN-05",  # Lista de enmiendas hechas a mano (administrativo)
        "GEN-26",  # Tablas de conversión (disponible online)
        # Mantenemos: GEN-27 (tablas sol), GEN-41/42 (tasas y derechos) según pedido del usuario
    ]
    
    download_folder = Path("aip_downloads")
    output_folder = Path("aip_output")
    output_folder.mkdir(exist_ok=True)
    
    writer = PdfWriter()
    total_size = 0
    included_files = []
    excluded_files = []
    
    # Obtener todos los archivos GEN y ordenar
    gen_files = sorted([f for f in download_folder.glob("GEN_*.pdf")])
    
    for pdf_file in gen_files:
        # Verificar si debe excluirse
        should_exclude = any(pattern in pdf_file.name for pattern in exclude_patterns)
        
        if should_exclude:
            excluded_files.append(pdf_file.name)
            print(f"❌ Excluido: {pdf_file.name}")
            continue
            
        try:
            with open(pdf_file, 'rb') as f:
                reader = PdfReader(f)
                
                # Agregar todas las páginas
                for page in reader.pages:
                    writer.add_page(page)
                    
                file_size = os.path.getsize(pdf_file)
                total_size += file_size
                included_files.append(pdf_file.name)
                print(f"✅ Incluido: {pdf_file.name} ({file_size/1024:.0f}KB)")
                
        except Exception as e:
            print(f"⚠️  Error con {pdf_file.name}: {e}")
            continue
    
    # Guardar PDF optimizado
    output_path = output_folder / "AIP_Argentina_GEN_Optimizado_v2.pdf"
    with open(output_path, 'wb') as f:
        writer.write(f)
    
    final_size = os.path.getsize(output_path)
    
    print(f"\n📊 RESULTADOS:")
    print(f"✅ Archivos incluidos: {len(included_files)}")
    print(f"❌ Archivos excluidos: {len(excluded_files)}")
    print(f"📁 Tamaño original estimado: {total_size/1024/1024:.1f}MB")
    print(f"📁 Tamaño final: {final_size/1024/1024:.1f}MB")
    print(f"💾 Reducción: {((157*1024*1024 - final_size)/(157*1024*1024))*100:.1f}%")
    print(f"\n📄 Archivo creado: {output_path}")
    
    return str(output_path)

if __name__ == "__main__":
    create_optimized_gen()
