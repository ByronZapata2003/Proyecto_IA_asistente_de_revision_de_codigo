# Reconstrucción frontend desde una captura

Aplicación educativa que recibe una captura JPG, PNG o WEBP (o captura una URL pública) y usa un modelo de visión de OpenAI para proponer HTML y CSS, más JavaScript cuando hace falta. **No es el asistente original de revisión de código**: el proyecto inicial contenía un modelo demostrativo basado en datos sintéticos, sin generación visual. Esa implementación no se presenta como si ya hiciera reconstrucción de interfaces; se retiró del flujo principal.

La imagen no revela el código fuente original. El resultado es una aproximación visual: puede diferir en tipografías, interacciones, diseño adaptable, recursos y elementos que no aparecen en la captura. El producto no afirma entrenar ningún modelo.

## Arquitectura

- **Streamlit**: carga de imagen/URL, comparación, código, descarga ZIP y gestión de proyectos.
- **FastAPI**: validación, captura con Playwright, llamada a OpenAI Responses API y endpoints de proyectos.
- **MongoDB local**: documentos en `web_screenshot_builder.projects`; se guarda fecha, origen, proveedor/modelo y código. No se guardan claves API ni la imagen original.
- **Vista previa**: documento generado dentro de un `iframe` con `sandbox="allow-scripts"` y origen opaco. El backend nunca ejecuta código generado.

## Requisitos en macOS

1. Instala Anaconda o Miniconda para macOS y MongoDB Community Server. Para inspeccionar datos, instala MongoDB Compass.
2. En Anaconda Terminal:

```bash
cd "/Users/javierlara/Documents/PROYECTO BD2/Proyecto_IA_asistente_de_revision_de_codigo/03_asistente_de_revision_de_codigo"
conda create -n screenshot-ui python=3.11 -y
conda activate screenshot-ui
python -m pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

3. Edita `.env` y configura `OPENAI_API_KEY` con una clave propia, `OPENAI_MODEL` con un modelo de visión disponible en tu cuenta y, si corresponde, `MONGO_URI`, `MONGO_DB` y `API_URL`. No pegues la clave en el notebook ni la subas al repositorio. El proveedor/modelo puede variar según acceso y cambios del servicio; el valor inicial es `gpt-4.1-mini`.
4. Inicia MongoDB localmente. Si instalaste Homebrew:

```bash
brew services start mongodb-community
```

Si usas el instalador oficial, inicia el servicio MongoDB según el método de instalación y confirma que escucha en `127.0.0.1:27017`.

## Iniciar la aplicación

Abre tres terminales, activa `conda activate screenshot-ui` y entra a la carpeta del proyecto en cada una.

**Terminal 1 — MongoDB**, solo si no está iniciado como servicio:

```bash
mongod --dbpath "$HOME/mongodb-data"
```

Crea esa carpeta antes si hace falta: `mkdir -p "$HOME/mongodb-data"`.

**Terminal 2 — API:**

```bash
uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 3 — interfaz:**

```bash
streamlit run frontend/app.py
```

Abre `http://localhost:8501`. La API está en `http://127.0.0.1:8000/docs`; `/health` muestra si hay clave configurada (nunca su valor). Los errores de API, proveedor o MongoDB indican el siguiente paso esperado.

### Captura de URL

Playwright usa Chromium headless, instalado con el comando anterior. Solo se aceptan URLs HTTP(S) cuyo dominio resuelva a IP pública. Sitios con inicio de sesión, CAPTCHA, bloqueo de automatización, navegación protegida o contenido dinámico pueden fallar o verse incompletos. La captura usa un viewport inicial de 1440×1000 y puede incluir toda la página; el modelo reconstruye lo visible en ella. No se permite usar esto para páginas internas o privadas.

### MongoDB Compass

Conecta Compass a `mongodb://127.0.0.1:27017` (o al URI configurado en `.env`). MongoDB crea la base `web_screenshot_builder` y la colección `projects` al guardar el primer proyecto. En Compass, actualiza las bases y abre `web_screenshot_builder > projects` para inspeccionar documentos. Cada documento incluye `created_at`, `source`, `provider`, `model`, `html`, `css` y `javascript`; no contiene la clave ni la imagen. Desde Streamlit se pueden listar, consultar y eliminar proyectos.

## Notebook

Desde la raíz de este proyecto y con el entorno activado:

```bash
jupyter lab
```

Abre `Laboratorio_IA.ipynb` y ejecuta en orden, celda por celda. El notebook no contiene salidas guardadas ni presupone archivos de ejemplo. Comprueba primero `.env`, API, MongoDB e imagen; las celdas que requieren recursos presentan instrucciones claras si faltan.

## Pruebas

Con el entorno activo, desde la raíz:

```bash
python -m pytest -q
```

Las pruebas cubren formatos/imágenes inválidas, falta de clave, límite de consulta y guardado de una respuesta simulada. No hacen llamadas pagadas al proveedor ni requieren un servidor MongoDB.

## Configuración y límites

- `.env.example` contiene solo nombres y valores locales no secretos. `.env` está pensado para permanecer local; verifica antes de publicar que no esté versionado.
- Límites predeterminados: imagen de hasta 10 MB y 25 megapíxeles; respuesta generada limitada a 500 KB por archivo. Ajusta `MAX_IMAGE_MB` y `URL_CAPTURE_TIMEOUT_SECONDS` en `.env` con valores razonables.
- No se guardan imágenes, URLs pueden incluir información sensible en el campo de origen, ni credenciales. Evita enviar capturas que contengan datos personales o secretos.
- Servicio local educativo, sin autenticación. No lo expongas a Internet.
