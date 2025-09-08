# 🚁 AIP Argentina - Inicio Rápido

## ⚡ Opción 1: Ejecución automática (recomendada)

```bash
# Hacer ejecutable y correr
chmod +x run.sh
./run.sh
```

## ⚙️ Opción 2: Paso a paso

```bash
# 1. Configurar entorno
python setup.py

# 2. Probar configuración
python test_scraper.py

# 3. Ejecutar scraper completo
python aip_scraper.py
```

## 📁 Archivos que obtienes

- **AIP_Argentina_Completo.pdf** - Todo en un archivo (si <100MB)
- **AIP_Argentina_GEN.pdf** - Sección Generalidades  
- **AIP_Argentina_ENR.pdf** - Sección En Ruta
- **AIP_Argentina_AD.pdf** - Sección Aeródromos (general + San Fernando)

## ⏱️ Tiempo estimado

- **Configuración inicial**: 2-5 minutos
- **Descarga y procesamiento**: 15-30 minutos
- **Total**: ~30-35 minutos

## 🎯 Contenido incluido

✅ **GEN**: Todos los documentos (reglamentos, tablas, códigos, servicios)  
✅ **ENR**: Todos los documentos (reglas, rutas, radioayudas, cartas)  
✅ **AD**: Páginas generales + **Todo sobre San Fernando (SADF)**

## 🔧 Requisitos mínimos

- Python 3.8+
- 500MB espacio libre
- Conexión a internet

## 🆘 Si algo falla

1. **Error de dependencias**: `python setup.py`
2. **Error de browser**: `python -m playwright install chromium`
3. **Archivos corruptos**: Borrar `aip_downloads/` y re-ejecutar
4. **Revisar logs**: Abrir `aip_scraper.log`

## 🎉 Resultado final

PDF navegable con:
- 📑 Índice clickeable
- 📖 Marcadores por sección
- 🔍 Texto searcheable (incluso en imágenes)
- 📊 Metadatos completos

---

💡 **Tip**: El script es inteligente y solo descarga documentos nuevos/actualizados en ejecuciones posteriores.
