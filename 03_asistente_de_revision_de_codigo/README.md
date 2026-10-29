# Reconstrucción de frontend desde capturas

Aplicación para generar una aproximación de frontend a partir de una captura JPG, PNG o WEBP, o de una URL pública. Streamlit recibe la entrada, FastAPI valida y captura la página cuando corresponde, un modelo de visión propone HTML/CSS/JavaScript y MongoDB guarda el resultado.

El notebook entrena un índice visual k-NN con pares captura/HTML de WebSight. Durante la generación, las capturas más cercanas se envían como ejemplos de referencia al modelo de visión. Esto es entrenamiento de recuperación contextual; no es un ajuste fino de un modelo generativo. La clave de OpenAI se usa para generar código y puede implicar consumo facturable. El HTML devuelto es una aproximación, no recupera el código fuente original.

## Requisitos

- Windows con Anaconda o Miniconda y Python 3.11.
- MongoDB Community Server instalado y ejecutándose localmente.
- Una clave de API de OpenAI con acceso a un modelo de visión.
- Conexión a Internet para instalar dependencias, obtener la muestra del dataset y generar código.

## Crear el entorno en Anaconda Prompt o CMD

Abre **Anaconda Prompt** (usa `cmd.exe`) en la raíz del repositorio y ejecuta:

```bat
cd /d "03_asistente_de_revision_de_codigo"
conda create -n screenshot-ui python=3.11 -y
conda activate screenshot-ui
python -m pip install -r requirements.txt
python -m playwright install chromium
copy .env.example .env
notepad .env
```

En `.env`, configura `OPENAI_API_KEY` y, si tu cuenta requiere otro modelo, `OPENAI_MODEL`. No publiques ese archivo. MongoDB usa `mongodb://127.0.0.1:27017` y la base `web_screenshot_builder` por defecto.

## Descargar el dataset y entrenar

Desde la carpeta `03_asistente_de_revision_de_codigo`, inicia Jupyter y abre `Laboratorio_IA.ipynb`:

```bat
jupyter lab
```

Ejecuta las celdas en orden. La descarga toma por defecto 128 pares de `HuggingFaceM4/WebSight` v0.2 y el notebook entrena `models/modelo.joblib`. Para elegir otra cantidad, edita `MAX_SAMPLES` en el notebook o llama `download_dataset(max_samples=...)`.

WebSight contiene pares sintéticos de capturas y HTML/Tailwind bajo CC BY 4.0. El corpus completo es muy grande; el modo streaming limita los ejemplos guardados, aunque el primer shard transferido puede ser de cientos de MB. La aplicación debe atribuir el dataset si se distribuye junto con el modelo o como aplicación de ML. [Ficha del dataset](https://huggingface.co/datasets/HuggingFaceM4/WebSight).

## Iniciar la aplicación

Deja MongoDB ejecutándose. Abre dos ventanas de Anaconda Prompt, activa el entorno y ejecuta ambos comandos desde la carpeta del proyecto.

**Ventana 1 — API:**

```bat
conda activate screenshot-ui
cd /d "03_asistente_de_revision_de_codigo"
uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

**Ventana 2 — interfaz:**

```bat
conda activate screenshot-ui
cd /d "03_asistente_de_revision_de_codigo"
streamlit run frontend/app.py
```

Abre `http://localhost:8501`. La documentación de FastAPI está en `http://127.0.0.1:8000/docs`; `/health` indica si está configurada la clave y si el índice del dataset fue entrenado.

## Verificación

Después de instalar las dependencias, ejecuta desde la carpeta del proyecto:

```bat
python -m pytest -q
```

Las pruebas no llaman a OpenAI ni requieren MongoDB para validar la generación simulada, el control de URL privada y el entrenamiento con pares locales temporales.

## Límites

- Solo se capturan URLs públicas accesibles sin autenticación; algunos sitios bloquean Playwright o renderizan contenido dinámico de forma incompleta.
- La generación requiere `OPENAI_API_KEY`, conexión al proveedor y un modelo con visión habilitado.
- El índice k-NN usa miniaturas RGB de 32×32: sirve como recuperación de referencias académica, no como modelo visual generativo ni como medida de similitud de alta fidelidad.
- La vista previa corre en un `iframe` aislado. Revisa el código generado antes de reutilizarlo.
