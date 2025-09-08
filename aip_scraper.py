#!/usr/bin/env python3
"""
AIP Argentina PDF Scraper and Combiner
Descarga y combina todos los PDFs del AIP de Argentina en un único documento con marcadores e índice.
"""

import asyncio
import os
import sys
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from urllib.parse import urljoin, urlparse
import json

import requests
from playwright.async_api import async_playwright, Page, Browser
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import fitz  # PyMuPDF for better PDF handling and OCR

# Configuración
BASE_URL = "https://ais.anac.gob.ar"
AIP_URL = f"{BASE_URL}/aip"
DOWNLOAD_FOLDER = Path("./aip_downloads")
OUTPUT_FOLDER = Path("./aip_output")
FINAL_PDF = "AIP_Argentina_Completo.pdf"
TEMP_FOLDER = Path("./temp_aip")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aip_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AIpDocument:
    """Representa un documento PDF del AIP"""
    def __init__(self, title: str, url: str, section: str, subsection: str = "", version: str = "", date: str = ""):
        self.title = title
        self.url = url
        self.section = section
        self.subsection = subsection
        self.version = version
        self.date = date
        self.filename = self._generate_filename()
        self.local_path = None
        
    def _generate_filename(self) -> str:
        """Genera un nombre de archivo limpio"""
        clean_title = re.sub(r'[^\w\s-]', '', self.title)
        clean_title = re.sub(r'\s+', '_', clean_title)
        return f"{self.section}_{clean_title}.pdf"
    
    def __str__(self):
        return f"{self.section}: {self.title} ({self.version})"

class AIPScraper:
    """Scraper principal para el sitio AIP de Argentina"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.documents: List[AIpDocument] = []
        
    async def scrape_section_documents(self, page: Page, section: str) -> List[AIpDocument]:
        """Extrae todos los documentos de una sección específica"""
        logger.info(f"Extrayendo documentos de la sección {section}")
        
        # Hacer clic en la sección correspondiente
        await page.click(f'a[href="/aip#{section.lower()}"]')
        await page.wait_for_timeout(2000)
        
        documents = []
        seen_documents = set()  # Para evitar duplicados
        page_num = 1
        
        while True:
            logger.info(f"Procesando página {page_num} de sección {section}")
            
            # Extraer documentos de la página actual
            rows = await page.query_selector_all('tbody tr')
            
            for row in rows:
                try:
                    title_cell = await row.query_selector('td:first-child')
                    link_cell = await row.query_selector('td:last-child a')
                    
                    if title_cell and link_cell:
                        title = await title_cell.inner_text()
                        version_date = await link_cell.inner_text()
                        href = await link_cell.get_attribute('href')
                        
                        if href and title:
                            # Crear identificador único para evitar duplicados
                            doc_id = f"{title.strip()}|{href}"
                            
                            # Filtrar documentos según criterios y evitar duplicados
                            if doc_id not in seen_documents and self._should_include_document(title, section):
                                url = urljoin(BASE_URL, href)
                                doc = AIpDocument(
                                    title=title.strip(),
                                    url=url,
                                    section=section,
                                    version=version_date.strip() if version_date else "",
                                    subsection=self._extract_subsection(title)
                                )
                                documents.append(doc)
                                seen_documents.add(doc_id)
                                logger.info(f"Documento agregado: {doc}")
                            
                except Exception as e:
                    logger.warning(f"Error procesando fila: {e}")
                    continue
            
            # Verificar si hay página siguiente
            next_button = await page.query_selector('text=Siguiente')
            if next_button and await next_button.is_enabled():
                # Verificar si realmente hay contenido diferente
                current_url = page.url
                await next_button.click()
                await page.wait_for_timeout(2000)
                
                # Si la URL no cambió o regresamos a la misma página, terminar
                new_url = page.url
                if current_url == new_url or page_num > 10:  # Límite de seguridad
                    break
                    
                page_num += 1
                
                # Límite adicional para evitar bucles infinitos
                if page_num > 20:
                    logger.warning(f"Límite de páginas alcanzado en sección {section}")
                    break
            else:
                break
                
        logger.info(f"Encontrados {len(documents)} documentos en sección {section}")
        return documents
    
    def _should_include_document(self, title: str, section: str) -> bool:
        """Determina si un documento debe ser incluido según los criterios"""
        if section in ['GEN', 'ENR', 'AD']:
            return True
        
        return False
    
    def _extract_subsection(self, title: str) -> str:
        """Extrae la subsección del título del documento"""
        match = re.match(r'^([A-Z]+-[\d.]+)', title)
        return match.group(1) if match else ""
    
    async def scrape_all_documents(self) -> List[AIpDocument]:
        """Extrae todos los documentos del sitio AIP"""
        logger.info("Iniciando scraping de documentos AIP")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(AIP_URL)
                await page.wait_for_load_state('networkidle')
                
                # Extraer documentos de cada sección
                sections = ['GEN', 'ENR', 'AD']
                for section in sections:
                    section_docs = await self.scrape_section_documents(page, section)
                    self.documents.extend(section_docs)
                    
                logger.info(f"Total de documentos encontrados: {len(self.documents)}")
                
            finally:
                await browser.close()
                
        return self.documents
    
    def download_document(self, document: AIpDocument) -> bool:
        """Descarga un documento PDF individual"""
        try:
            logger.info(f"Descargando: {document.title}")
            
            response = self.session.get(document.url, timeout=60)
            response.raise_for_status()
            
            # Verificar que es un PDF
            if 'application/pdf' not in response.headers.get('content-type', ''):
                logger.warning(f"El archivo no es un PDF: {document.title}")
                return False
            
            # Guardar archivo
            DOWNLOAD_FOLDER.mkdir(exist_ok=True)
            file_path = DOWNLOAD_FOLDER / document.filename
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            document.local_path = file_path
            logger.info(f"Descargado exitosamente: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error descargando {document.title}: {e}")
            return False
    
    def download_all_documents(self) -> int:
        """Descarga todos los documentos encontrados"""
        logger.info("Iniciando descarga de documentos")
        
        successful_downloads = 0
        for doc in self.documents:
            if self.download_document(doc):
                successful_downloads += 1
                
        logger.info(f"Descargados exitosamente: {successful_downloads}/{len(self.documents)}")
        return successful_downloads

class PDFCombiner:
    """Combina múltiples PDFs en uno solo con marcadores e índice"""
    
    def __init__(self, documents: List[AIpDocument]):
        self.documents = documents
        self.toc_entries = []  # Tabla de contenidos
        
    def create_index_pdf(self) -> str:
        """Crea un PDF con el índice de contenidos"""
        TEMP_FOLDER.mkdir(exist_ok=True)
        index_path = TEMP_FOLDER / "indice.pdf"
        
        # Configurar documento
        doc = SimpleDocTemplate(
            str(index_path),
            pagesize=A4,
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch,
            bottomMargin=inch
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading1'],
            fontSize=14,
            leftIndent=0,
            spaceAfter=12
        )
        
        subsection_style = ParagraphStyle(
            'SubsectionStyle',
            parent=styles['Heading2'],
            fontSize=12,
            leftIndent=20,
            spaceAfter=8
        )
        
        # Contenido del índice
        story = []
        story.append(Paragraph("ÍNDICE DE CONTENIDOS", title_style))
        story.append(Paragraph("Publicación de Información Aeronáutica (AIP) - República Argentina", styles['Normal']))
        story.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Agrupar documentos por sección
        sections = self._group_documents_by_section()
        page_num = 3  # Empezar después del índice
        
        for section_name, docs in sections.items():
            story.append(Paragraph(f"{section_name}", section_style))
            
            for doc in docs:
                title = doc.title.replace(f"{section_name}-", "").strip()
                if len(title) > 80:
                    title = title[:80] + "..."
                
                entry = Paragraph(
                    f"{title} ..................................... {page_num}",
                    subsection_style
                )
                story.append(entry)
                
                # Estimar páginas del documento (aproximado)
                if doc.local_path and doc.local_path.exists():
                    try:
                        pdf = PdfReader(str(doc.local_path))
                        page_num += len(pdf.pages)
                    except:
                        page_num += 5  # Estimación por defecto
                else:
                    page_num += 5
                    
                # Almacenar entrada para TOC
                self.toc_entries.append({
                    'title': title,
                    'section': section_name,
                    'page': page_num - (len(pdf.pages) if 'pdf' in locals() and pdf else 5)
                })
                
            story.append(Spacer(1, 12))
        
        # Generar PDF
        doc.build(story)
        logger.info(f"Índice creado: {index_path}")
        return str(index_path)
    
    def _group_documents_by_section(self) -> Dict[str, List[AIpDocument]]:
        """Agrupa documentos por sección manteniendo orden jerárquico"""
        sections = {'GEN': [], 'ENR': [], 'AD': []}
        
        for doc in self.documents:
            if doc.local_path and doc.local_path.exists():
                sections[doc.section].append(doc)
        
        # Ordenar documentos dentro de cada sección
        for section in sections:
            sections[section].sort(key=lambda x: x.title)
            
        return sections
    
    def apply_ocr_if_needed(self, pdf_path: str) -> str:
        """Aplica OCR al PDF si contiene imágenes sin texto"""
        try:
            doc = fitz.open(pdf_path)
            needs_ocr = False
            
            # Verificar si hay páginas con poco texto pero con imágenes
            for page_num, page in enumerate(doc):
                text = page.get_text()
                images = page.get_images()
                
                if len(images) > 0 and len(text.strip()) < 100:
                    needs_ocr = True
                    break
            
            if needs_ocr:
                logger.info(f"Aplicando OCR a: {pdf_path}")
                ocr_path = str(Path(pdf_path).with_suffix('.ocr.pdf'))
                
                # Aplicar OCR usando PyMuPDF
                doc_ocr = fitz.open()
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    
                    # Renderizar página como imagen
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    
                    # Crear nueva página con imagen y texto OCR
                    new_page = doc_ocr.new_page(width=page.rect.width, height=page.rect.height)
                    new_page.insert_image(page.rect, stream=img_data)
                    
                    # Intentar extraer texto con OCR (requiere tesseract)
                    try:
                        import pytesseract
                        from PIL import Image
                        import io
                        
                        img = Image.open(io.BytesIO(img_data))
                        ocr_text = pytesseract.image_to_string(img, lang='spa')
                        
                        if ocr_text.strip():
                            # Agregar texto invisible para búsqueda
                            text_dict = {
                                "fontsize": 12,
                                "fontname": "helv",
                                "color": (1, 1, 1)  # Texto blanco (invisible)
                            }
                            new_page.insert_text((50, 50), ocr_text, **text_dict)
                            
                    except ImportError:
                        logger.warning("pytesseract no disponible, OCR omitido")
                    except Exception as e:
                        logger.warning(f"Error en OCR para página {page_num}: {e}")
                
                doc_ocr.save(ocr_path)
                doc_ocr.close()
                doc.close()
                
                return ocr_path
            
            doc.close()
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error aplicando OCR a {pdf_path}: {e}")
            return pdf_path
    
    def combine_pdfs(self) -> str:
        """Combina todos los PDFs en uno solo con marcadores"""
        logger.info("Iniciando combinación de PDFs")
        
        OUTPUT_FOLDER.mkdir(exist_ok=True)
        output_path = OUTPUT_FOLDER / FINAL_PDF
        
        # Crear índice
        index_path = self.create_index_pdf()
        
        # Inicializar writer
        writer = PdfWriter()
        
        # Agregar índice
        with open(index_path, 'rb') as f:
            index_pdf = PdfReader(f)
            for page in index_pdf.pages:
                writer.add_page(page)
            
            # Agregar marcador para índice
            writer.add_outline_item("Índice de Contenidos", 0)
        
        current_page = len(index_pdf.pages)
        sections = self._group_documents_by_section()
        
        # Combinar documentos por sección
        for section_name, docs in sections.items():
            section_bookmark = writer.add_outline_item(section_name, current_page)
            
            for doc in docs:
                if not doc.local_path or not doc.local_path.exists():
                    logger.warning(f"Archivo no encontrado: {doc.title}")
                    continue
                
                try:
                    # Aplicar OCR si es necesario
                    pdf_path = self.apply_ocr_if_needed(str(doc.local_path))
                    
                    # Agregar PDF
                    with open(pdf_path, 'rb') as f:
                        pdf = PdfReader(f)
                        
                        # Agregar marcador para documento
                        title = doc.title.replace(f"{section_name}-", "").strip()
                        writer.add_outline_item(title, current_page, parent=section_bookmark)
                        
                        # Agregar páginas
                        for page in pdf.pages:
                            writer.add_page(page)
                            
                        current_page += len(pdf.pages)
                        logger.info(f"Agregado: {doc.title} ({len(pdf.pages)} páginas)")
                        
                    # Limpiar archivo OCR temporal si fue creado
                    if pdf_path != str(doc.local_path):
                        os.unlink(pdf_path)
                        
                except Exception as e:
                    logger.error(f"Error agregando {doc.title}: {e}")
                    continue
        
        # Guardar PDF final
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        logger.info(f"PDF combinado creado: {output_path}")
        logger.info(f"Total de páginas: {current_page}")
        
        # Verificar tamaño del archivo
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Tamaño del archivo: {file_size_mb:.1f} MB")
        
        if file_size_mb > 100:
            logger.warning(f"El archivo supera los 100MB ({file_size_mb:.1f}MB). Consider dividirlo por secciones.")
        
        return str(output_path)
    
    def create_sectioned_pdfs(self) -> List[str]:
        """Crea PDFs separados por sección si el archivo es muy grande"""
        logger.info("Creando PDFs por sección")
        
        OUTPUT_FOLDER.mkdir(exist_ok=True)
        output_files = []
        sections = self._group_documents_by_section()
        
        for section_name, docs in sections.items():
            if not docs:
                continue
                
            section_output = OUTPUT_FOLDER / f"AIP_Argentina_{section_name}.pdf"
            writer = PdfWriter()
            
            # Agregar marcador de sección
            current_page = 0
            section_bookmark = writer.add_outline_item(section_name, 0)
            
            for doc in docs:
                if not doc.local_path or not doc.local_path.exists():
                    continue
                
                try:
                    pdf_path = self.apply_ocr_if_needed(str(doc.local_path))
                    
                    with open(pdf_path, 'rb') as f:
                        pdf = PdfReader(f)
                        
                        title = doc.title.replace(f"{section_name}-", "").strip()
                        writer.add_outline_item(title, current_page, parent=section_bookmark)
                        
                        for page in pdf.pages:
                            writer.add_page(page)
                            
                        current_page += len(pdf.pages)
                        
                    if pdf_path != str(doc.local_path):
                        os.unlink(pdf_path)
                        
                except Exception as e:
                    logger.error(f"Error agregando {doc.title} a sección {section_name}: {e}")
                    continue
            
            # Guardar PDF de sección
            with open(section_output, 'wb') as f:
                writer.write(f)
                
            output_files.append(str(section_output))
            file_size_mb = os.path.getsize(section_output) / (1024 * 1024)
            logger.info(f"PDF de sección creado: {section_output} ({file_size_mb:.1f} MB)")
            
        return output_files

def save_metadata(documents: List[AIpDocument], output_folder: Path):
    """Guarda metadatos de los documentos descargados"""
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'total_documents': len(documents),
        'documents': []
    }
    
    for doc in documents:
        doc_info = {
            'title': doc.title,
            'section': doc.section,
            'subsection': doc.subsection,
            'version': doc.version,
            'url': doc.url,
            'filename': doc.filename,
            'downloaded': doc.local_path is not None and doc.local_path.exists()
        }
        metadata['documents'].append(doc_info)
    
    metadata_path = output_folder / 'metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Metadatos guardados: {metadata_path}")

async def main():
    """Función principal"""
    logger.info("=== Iniciando AIP Argentina Scraper ===")
    
    try:
        # Inicializar scraper
        scraper = AIPScraper()
        
        # Extraer documentos
        documents = await scraper.scrape_all_documents()
        
        if not documents:
            logger.error("No se encontraron documentos")
            return
        
        # Descargar documentos
        successful_downloads = scraper.download_all_documents()
        
        if successful_downloads == 0:
            logger.error("No se pudieron descargar documentos")
            return
        
        # Filtrar solo documentos descargados exitosamente
        downloaded_docs = [doc for doc in documents if doc.local_path and doc.local_path.exists()]
        
        # Combinar PDFs
        combiner = PDFCombiner(downloaded_docs)
        
        # Intentar crear PDF combinado
        try:
            final_pdf = combiner.combine_pdfs()
            
            # Verificar tamaño
            file_size_mb = os.path.getsize(final_pdf) / (1024 * 1024)
            if file_size_mb > 100:
                logger.info("Archivo muy grande, creando PDFs por sección...")
                sectioned_pdfs = combiner.create_sectioned_pdfs()
                logger.info(f"PDFs por sección creados: {sectioned_pdfs}")
            else:
                logger.info(f"PDF final creado exitosamente: {final_pdf}")
                
        except Exception as e:
            logger.error(f"Error creando PDF combinado: {e}")
            logger.info("Creando PDFs por sección como alternativa...")
            sectioned_pdfs = combiner.create_sectioned_pdfs()
            logger.info(f"PDFs por sección creados: {sectioned_pdfs}")
        
        # Guardar metadatos
        save_metadata(downloaded_docs, OUTPUT_FOLDER)
        
        logger.info("=== Proceso completado exitosamente ===")
        logger.info(f"Documentos procesados: {len(downloaded_docs)}")
        logger.info(f"Archivos de salida en: {OUTPUT_FOLDER}")
        
    except Exception as e:
        logger.error(f"Error en proceso principal: {e}")
        raise

if __name__ == "__main__":
    # Verificar dependencias
    required_packages = [
        ('playwright', 'playwright'),
        ('PyPDF2', 'PyPDF2'), 
        ('reportlab', 'reportlab'), 
        ('requests', 'requests'), 
        ('fitz', 'PyMuPDF')  # PyMuPDF se importa como fitz
    ]
    
    missing_packages = []
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("Paquetes faltantes:")
        for package in missing_packages:
            print(f"  pip install {package}")
        print("\nPara instalar todos:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    # Ejecutar
    asyncio.run(main())
