# Reconstrucción frontend desde una captura

Aplicación educativa que recibe una captura JPG, PNG o WEBP (o captura una URL pública) y usa un modelo de visión de Gemini u OpenAI para proponer HTML y CSS, más JavaScript cuando hace falta. Gemini queda como proveedor de ejemplo para probar el nivel gratuito si está disponible para tu proyecto. **No es el asistente original de revisión de código**: el proyecto inicial contenía un modelo demostrativo basado en datos sintéticos, sin generación visual. Esa implementación no se presenta como si ya hiciera reconstrucción de interfaces; se retiró del flujo principal.

La imagen no revela el código fuente original. El resultado es una aproximación visual: puede diferir en tipografías, interacciones, diseño adaptable, recursos y elementos que no aparecen en la captura. El índice opcional de referencias aprende similitudes visuales; no ajusta los pesos de ningún modelo generativo.

## Arquitectura

- **Streamlit**: carga de imagen/URL, comparación, código, descarga ZIP y gestión de proyectos.
- **FastAPI**: validación, captura con Playwright, llamada a Gemini `generateContent` u OpenAI Responses API y endpoints de proyectos.
- **MongoDB**: local o Atlas; documentos en `web_screenshot_builder.projects` con fecha, origen, proveedor/modelo y código. No se guardan claves API ni la imagen original.
- **Vista previa**: documento generado dentro de un `iframe` con `sandbox="allow-scripts"` y origen opaco. El backend nunca ejecuta código generado.

## Referencias opcionales de WebSight

La app puede usar un índice visual k-NN de pares de captura/HTML de [HuggingFaceM4/WebSight](https://huggingface.co/datasets/HuggingFaceM4/WebSight) para añadir ejemplos estructurales al contexto del proveedor. Esto es recuperación de ejemplos, no ajuste fino de Gemini ni OpenAI. Sin el índice entrenado, la reconstrucción funciona directamente con la imagen.

Desde esta carpeta y con el entorno Conda activado, descarga una muestra limitada y crea el índice local:

```bash
python -c "from descargar_dataset import download_dataset; print(download_dataset(max_samples=128))"
python -c "from backend.ml import train; model = train(); print('Índice entrenado con', len(model['examples']), 'pares')"
```

La primera descarga puede transferir un shard remoto grande aunque se guarde una muestra pequeña. El dataset tiene licencia CC BY 4.0; conserva la atribución si distribuyes el modelo o la aplicación. El índice se guarda localmente en `models/` y no debe subirse al repositorio.

## Preparar el entorno en macOS

1. Instala Anaconda o Miniconda para macOS y MongoDB Community Server. Para inspeccionar datos, instala MongoDB Compass.
2. En Anaconda Terminal:

```bash
cd "/ruta/al/repositorio/03_asistente_de_revision_de_codigo"
conda create -n screenshot-ui python=3.11 -y
conda activate screenshot-ui
python -m pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

3. Para probar Gemini, crea una clave en [Google AI Studio](https://aistudio.google.com/app/apikey), y configura en `.env` `AI_PROVIDER=gemini`, `GEMINI_API_KEY` y `GEMINI_MODEL` (la plantilla propone `gemini-1.5-flash`). La API de Gemini ofrece un nivel gratuito para ciertos modelos y cuentas elegibles, con cuotas que pueden cambiar; confirma que el proyecto esté en el nivel gratuito en AI Studio. En ese nivel Google puede usar el contenido enviado para mejorar sus productos, así que evita capturas sensibles. Si prefieres OpenAI, usa `AI_PROVIDER=openai`, `OPENAI_API_KEY` y `OPENAI_MODEL`. No pegues claves en el notebook ni las subas al repositorio. También configura `MONGO_URI`, `MONGO_DB` y `API_URL` si necesitas cambiar los valores locales.
4. Inicia MongoDB localmente. Si instalaste Homebrew:

```bash
brew services start mongodb-community
```

Si usas el instalador oficial, inicia el servicio MongoDB según el método de instalación y confirma que escucha en `127.0.0.1:27017`. Este paso solo aplica cuando usas MongoDB local.

## Preparar el entorno en Windows

Abre **Anaconda Prompt** en la raíz del repositorio y ejecuta:

```bat
cd /d "03_asistente_de_revision_de_codigo"
conda create -n screenshot-ui python=3.11 -y
conda activate screenshot-ui
python -m pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
notepad .env
```

Completa `.env` con la clave del proveedor elegido y la URI de Atlas o la URI de MongoDB local. No publiques `.env` ni pegues claves en el notebook.

## Configurar MongoDB Atlas

1. Crea un cluster de Atlas y un usuario de base de datos con permisos de lectura y escritura.
2. En **Network Access**, permite la IP pública desde la que ejecutarás la API. Si cambia tu red, actualiza la regla; evita `0.0.0.0/0` salvo que necesites y comprendas el acceso desde cualquier IP.
3. En **Connect → Drivers**, copia la URI para Python/PyMongo. Pégala como `MONGO_URI` en `.env` y sustituye el usuario, la contraseña y el host del cluster. Si la contraseña incluye caracteres especiales, codifícalos para URL.
4. Deja `MONGO_DB=web_screenshot_builder` o elige otro nombre. La base y la colección `projects` se crean al guardar el primer proyecto.

La plantilla `.env.example` deja una URI de Atlas lista para completar. No inicies la API hasta sustituir todos sus campos. Para usar MongoDB local, configura `MONGO_URI=mongodb://127.0.0.1:27017`; si usas Atlas, no hace falta iniciar un servidor MongoDB local.

## Iniciar la aplicación

Abre tres terminales, activa `conda activate screenshot-ui` y entra a la carpeta del proyecto en cada una. Si usas Atlas, omite el terminal de MongoDB local.

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

Para cambiar proveedor, edita `AI_PROVIDER` y la clave/modelo correspondientes en `.env`, guarda y reinicia FastAPI. Para una prueba sin cargo, asegúrate de que `GEMINI_API_KEY` pertenezca a un proyecto de AI Studio elegible para el nivel gratuito; las cuotas y los modelos habilitados dependen de Google y pueden variar. El uso por encima del nivel gratuito puede generar cargos si el proyecto está vinculado a facturación.

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

Las pruebas cubren formatos/imágenes inválidas, falta de clave, límite de consulta, guardado y respuesta de URL con vista previa, y entrenamiento/recuperación con muestras simuladas. No hacen llamadas pagadas al proveedor, descargan datasets ni requieren un servidor MongoDB.

## Configuración y límites

- `.env.example` contiene solo nombres y valores locales no secretos. `.env` está pensado para permanecer local; verifica antes de publicar que no esté versionado.
- Límites predeterminados: imagen de hasta 10 MB y 25 megapíxeles; respuesta generada limitada a 500 KB por archivo. Ajusta `MAX_IMAGE_MB` y `URL_CAPTURE_TIMEOUT_SECONDS` en `.env` con valores razonables.
- No se guardan imágenes, URLs pueden incluir información sensible en el campo de origen, ni credenciales. Evita enviar capturas que contengan datos personales o secretos.
- Servicio local educativo, sin autenticación. No lo expongas a Internet.
