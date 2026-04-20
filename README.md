# Reaper Text Project Builder

Generador de sesiones **REAPER `.rpp`** desde texto/estructura de carpetas, pensado para pipelines de locución/SFX.

## Qué se tomó como referencia de tus archivos

En el repo hay dos ejemplos:

- `sesion_vacia.rpp`: proyecto base sin tracks/items.
- `track_files_chains.rpp`: proyecto con tracks, items con `FILE` por item, envolvente de volumen y cadena de FabFilter.

Este proyecto replica esos bloques estructurales para construir sesiones automáticamente.

## Funcionalidades

- Escanea una carpeta raíz con audio (incluye subcarpetas).
- Convierte la estructura de carpetas en tracks jerárquicos (canales/subcanales).
- Crea items con `SOURCE WAVE` y `FILE` apuntando a cada audio.
- Crea automatización **Pre-FX volume** (envolvente de track) desde `min dB` a `max dB` entre primer y último item del track.
- Inserta cadena de FX FabFilter configurable:
  - Pro-DS
  - Pro-C 2
  - Pro-Q 3
  - Pro-MB
  - Pro-L 2
- Permite ordenar items por script externo (CSV/XLSX/TXT, primera columna).
- Incluye GUI simple en PySide6.

## Estructura

- `reaper_text_project/models.py`: clases `Project`, `Track`, `Item`, `VolumeEnvelope`, `FXChain`.
- `reaper_text_project/generator.py`: lógica de escaneo, orden y render de proyecto.
- `reaper_text_project/script_order.py`: lector de orden desde CSV/XLSX/TXT.
- `reaper_text_project/cli.py`: interfaz por línea de comandos.
- `reaper_text_project/gui.py`: interfaz gráfica PySide6.
- `tests/test_generator.py`: prueba básica de generación.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# opcional para Excel
pip install openpyxl
```

## Uso CLI

```bash
reaper-rpp /ruta/audios /ruta/salida/proyecto.rpp \
  --min-db -3 --max-db 3 --spacing 2.0 \
  --script /ruta/script.xlsx
```

Desactivar FX completos:

```bash
reaper-rpp /ruta/audios /ruta/salida/proyecto.rpp --no-fx
```

Desactivar plugins puntuales:

```bash
reaper-rpp /ruta/audios /ruta/salida/proyecto.rpp --no-eq --no-limiter
```

## Uso GUI

```bash
reaper-rpp-gui
# o
python -m reaper_text_project
```

En la GUI:
1. Selecciona carpeta raíz de audio.
2. Selecciona ruta de salida `.rpp`.
3. (Opcional) archivo de script para orden.
4. Ajusta rango dB de automatización y spacing.
5. Activa/desactiva cadena FX y procesos.
6. Genera.

## Notas importantes

- El largo de cada item se estima por tamaño de archivo (sin dependencias de audio extra) para mantener el flujo simple.
- Si quieres duración exacta por archivo, puedes integrar `soundfile`/`pydub` fácilmente en `guessed_item_length()`.
- En REAPER, si algún plugin FabFilter no está instalado, el bloque quedará en la sesión pero ese FX puede aparecer offline.

## Roadmap sugerido

- Parseador completo `.rpp` para importar/editar proyectos existentes.
- Perfiles de cadena FX por tipo de carpeta (VO, SFX, Music, etc).
- Soporte de markers/regiones a partir del script.
- Exportación de reportes de conformado (JSON/CSV).
