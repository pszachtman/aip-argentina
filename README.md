# AIP Argentina Scraper

Script automatizado para descargar y combinar todos los PDFs del AIP (Publicación de Información Aeronáutica) de Argentina en un único documento navegable.

## 🚀 Características

- **Descarga automática** de todos los PDFs de las secciones GEN, ENR y AD
- **Filtrado inteligente** incluye páginas generales de AD y todos los documentos del aeropuerto San Fernando (SADF)
- **Combinación de PDFs** con estructura jerárquica y marcadores navegables
- **Índice de contenidos** con hipervínculos para navegación rápida
- **OCR automático** para imágenes que contienen texto (requiere Tesseract)
- **Manejo de archivos grandes** con opción de dividir por secciones
- **Metadatos completos** de todos los documentos procesados
- **Logging detallado** para seguimiento del progreso

## 📋 Requisitos

- Python 3.8 o superior
- Conexión a internet estable
- 1-2 GB de espacio libre en disco (para todos los aeródromos)

### Dependencias opcionales
- Tesseract OCR (para mejor reconocimiento de texto en imágenes)

## 🔧 Instalación

### Opción 1: Instalación automática (recomendada)

```bash
# Clonar o descargar los archivos del proyecto
cd aip-argentina

# Ejecutar configuración automática
python setup.py
```

### Opción 2: Instalación manual

```bash
# Instalar dependencias de Python
pip install -r requirements.txt

# Instalar browsers de Playwright
python -m playwright install chromium

# Instalar Tesseract (opcional, para OCR completo)
# macOS:
brew install tesseract tesseract-lang

# Ubuntu/Debian:
sudo apt install tesseract-ocr tesseract-ocr-spa

# Windows: descargar desde https://github.com/UB-Mannheim/tesseract/wiki
```

## 🚀 Uso

### Ejecución básica

```bash
python aip_scraper.py
```

### Estructura de archivos generados

```
aip-argentina/
├── aip_downloads/          # PDFs individuales descargados
├── aip_output/             # PDFs finales combinados
│   ├── AIP_Argentina_Completo.pdf    # PDF único (si <100MB)
│   ├── AIP_Argentina_GEN.pdf         # PDF por secciones
│   ├── AIP_Argentina_ENR.pdf
│   ├── AIP_Argentina_AD.pdf
│   └── metadata.json                 # Metadatos de documentos
├── temp_aip/               # Archivos temporales
└── aip_scraper.log         # Log detallado del proceso
```

## 📚 Contenido incluido

### Sección GEN (Generalidades)
- ✅ Todos los documentos (prefacio, registros, tablas, códigos, servicios, tasas)

### Sección ENR (En Ruta)
- ✅ Todos los documentos (reglas, procedimientos, espacio aéreo, rutas, radioayudas, alertas, cartas)

### Sección AD (Aeródromos)
- ✅ **TODOS los documentos** de aeródromos (páginas generales + todos los aeródromos específicos)
- ✅ Incluye: SADF (San Fernando), SABE (Jorge Newbery), SACO (Córdoba), SADF (San Fernando), y TODOS los demás

## ⚙️ Configuración avanzada

### 📉 Optimización de tamaño de archivos

Si el archivo GEN (157MB) es demasiado grande, puedes crear una versión optimizada:

```bash
# Crear versión optimizada del GEN (solo ~21MB)
python optimize_gen.py
```

**Versión optimizada incluye:**
- ✅ Todos los reglamentos y servicios esenciales
- ✅ Tablas de salida/puesta del sol
- ✅ Tasas y derechos de aeródromos
- ❌ Excluye solo registros administrativos

**Resultado:** `AIP_Argentina_GEN_Optimizado_v2.pdf` (21MB vs 157MB original)

### Modificar criterios de filtrado (si es necesario)

Por defecto, el script incluye **TODOS** los documentos de las tres secciones (GEN, ENR, AD). Si quisieras filtrar algunos aeródromos específicos, puedes editar la función `_should_include_document()` en `aip_scraper.py`:

```python
def _should_include_document(self, title: str, section: str) -> bool:
    if section in ['GEN', 'ENR']:
        return True
    if section == 'AD':
        # Ejemplo: excluir aeródromos específicos si el archivo fuera muy grande
        # if 'UNWANTED_CODE' in title:
        #     return False
        return True  # Por defecto incluye todo
```

### Configurar tamaño máximo del archivo

Modifica la constante en el script:

```python
MAX_FILE_SIZE_MB = 100  # Cambiar según necesidades
```

## 🔍 Características del PDF final

- **Marcadores jerárquicos** organizados por secciones y subsecciones
- **Índice navegable** con hipervínculos a cada documento
- **Texto searcheable** incluyendo contenido extraído de imágenes (OCR)
- **Metadatos incluidos** con fechas de generación y versiones
- **Estructura mantenida** respetando la organización original del AIP

## 📝 Logging y diagnóstico

El script genera un archivo de log detallado (`aip_scraper.log`) que incluye:

- URLs procesadas y documentos encontrados
- Estado de descargas (exitosas/fallidas)
- Proceso de combinación de PDFs
- Aplicación de OCR cuando sea necesario
- Errores y advertencias detalladas

## 🛠️ Solución de problemas

### Error: "Browser not found"
```bash
python -m playwright install chromium
```

### Error: "pytesseract not found"
El OCR es opcional. Para habilitarlo:
- macOS: `brew install tesseract`
- Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-spa`

### Archivo PDF muy grande
El script automáticamente dividirá en archivos por sección si supera los 100MB.

### Descargas lentas o fallan
- Verificar conexión a internet
- El script incluye reintentos automáticos
- Revisar logs para identificar documentos problemáticos

### Error de memoria al combinar PDFs
- Reducir la cantidad de documentos incluidos
- Usar PDFs por sección en lugar del archivo único

## 🔄 Actualizaciones futuras

Para actualizar con las últimas versiones del AIP:

```bash
# Eliminar descargas previas (opcional)
rm -rf aip_downloads/*

# Re-ejecutar scraper
python aip_scraper.py
```

El script detectará automáticamente nuevas versiones comparando los metadatos.

## 📊 Estadísticas típicas

- **Documentos GEN**: ~30 PDFs
- **Documentos ENR**: ~45 PDFs  
- **Documentos AD completos**: ~50 PDFs (todos los aeródromos)
- **Tiempo de ejecución**: 30-60 minutos
- **Tamaño final**: 
  - GEN: 157MB (completo) / 21MB (optimizado)
  - ENR: ~50MB
  - AD: ~90MB
  - **Total**: ~300MB

## 🤝 Contribuciones

Este es un proyecto de código abierto. Las mejoras son bienvenidas:

1. Optimización de filtros de documentos
2. Mejora en el reconocimiento OCR
3. Interfaz gráfica para configuración
4. Soporte para otros países/AIPs
5. Automatización de actualizaciones periódicas

## ⚖️ Consideraciones legales

- Este script está diseñado para uso personal/profesional legítimo
- Los documentos AIP son públicos y están disponibles en el sitio oficial de ANAC
- Respeta los términos de servicio del sitio web
- El script incluye delays apropiados para no sobrecargar el servidor

## 📞 Soporte

Para problemas o mejoras:
1. Revisar logs detallados en `aip_scraper.log`
2. Verificar configuración con `python setup.py`
3. Consultar esta documentación para soluciones comunes

---

**Nota**: Este proyecto no está afiliado oficialmente con ANAC (Administración Nacional de Aviación Civil de Argentina). Es una herramienta independiente para facilitar el acceso a información públicamente disponible.
