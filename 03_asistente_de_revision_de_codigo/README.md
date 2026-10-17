# Asistente de revisión de código

**Curso:** Inteligencia Artificial  
**Docente:** Julian Rene Muñoz Burbano

## Alcance
Prototipo educativo integrable: Streamlit + FastAPI + MongoDB + modelo de referencia `imagen`. **No es la implementacion especifica integral de todos los requisitos del PDF**: el modelo es un baseline sintetico y debe sustituirse por datos y logica propios del caso.

## Instalacion Windows / Anaconda
```bat
conda create -n IA_C1_P03 python=3.11 -y
conda activate IA_C1_P03
python -m pip install -r requirements.txt
copy .env.example .env
```
Instale y arranque MongoDB Community Server en localhost:27017.

## Ejecucion
En la carpeta del proyecto, en dos terminales del mismo entorno:
```bat
uvicorn backend.api:app --reload --port 8000
streamlit run frontend/app.py
```
Frontend: http://localhost:8501 · API: http://localhost:8000/docs

## Notebook y pruebas
Abra `jupyter lab` y ejecute `Laboratorio_IA.ipynb` desde la carpeta del proyecto. `python -m pytest -q` verifica el baseline. Cada proyecto usa su propia base `ia_c1_p03`. Use puertos diferentes si inicia varios proyectos simultaneamente.

## Limites
No incluye datos reales, integraciones externas ni un modelo entrenado especifico para el dominio. La primera ejecucion entrena automaticamente el baseline. No exponga API/MongoDB a Internet sin autenticacion, TLS y controles de acceso.

## Dataset sugerido
- **Fuente:** CodeSearchNet
- **URL:** https://github.com/github/CodeSearchNet
- **Modo:** consulta/descarga manual (puede requerir registro o aceptación de licencia)
- Ejecutar `python descargar_dataset.py` desde esta carpeta.
- Los datos externos no se conectan todavía al entrenamiento del baseline existente; adapte las columnas y el pipeline antes de afirmar que se entrenó con el dataset.
