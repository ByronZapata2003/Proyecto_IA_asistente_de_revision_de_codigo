from __future__ import annotations
import html
import io
import os
import zipfile
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
API = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="Reconstrucción de páginas", page_icon="🖼️", layout="wide")
st.title("Reconstruye una página desde una captura")
st.caption("Genera archivos frontend con un modelo de visión. La captura no contiene el código fuente original: fuentes, interacciones, adaptación responsive y contenido no visible pueden diferir.")


def explain_error(exc):
    if isinstance(exc, requests.HTTPError):
        try: 
            st.error(exc.response.json().get("detail", str(exc)))
        except Exception: 
            st.error(str(exc))
    elif isinstance(exc, requests.Timeout):
        st.warning(
            "La solicitud tardó más de lo esperado. La API podría seguir procesándola y guardar el proyecto; "
            "revisa Proyectos guardados antes de volver a enviarla."
        )
    else:
        st.error(f"No se pudo conectar con la API en {API}. Inicia FastAPI y revisa API_URL. Detalle: {exc}")


def bundle(project):
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "index.html", 
            '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="Styles/style.css"><title>Reconstrucción</title></head><body>\n' 
            + project["html"] + 
            '\n<script src="Scripts/main.js"></script></body></html>'
        )
        z.writestr("Styles/style.css", project["css"])
        if project.get("javascript") and project["javascript"].strip() != "(vacío)":
            z.writestr("Scripts/main.js", project["javascript"])
        if "arbol_estructura" in project:
            z.writestr("estructura.txt", project["arbol_estructura"])
    return mem.getvalue()


tab_new, tab_projects = st.tabs(["Crear reconstrucción", "Proyectos guardados"])

with tab_new:
    mode = st.radio("Origen", ["Subir capturas", "Capturar URL pública"], horizontal=True)
    
    if mode == "Subir capturas":
        if "num_capturas" not in st.session_state:
            st.session_state["num_capturas"] = 1

        uploaded_files = []
        
        for i in range(st.session_state["num_capturas"]):
            file_uploaded = st.file_uploader(
                f"Subir Imagen {i + 1}", 
                type=["jpg", "jpeg", "png", "webp"], 
                key=f"uploader_{i}"
            )
            if file_uploaded:
                uploaded_files.append(file_uploaded)

        st.button("➕ Subir otra captura", on_click=lambda: st.session_state.update({"num_capturas": st.session_state["num_capturas"] + 1}))

        if uploaded_files:
            st.subheader("Capturas seleccionadas")
            cols = st.columns(min(len(uploaded_files), 4))
            for idx, img_file in enumerate(uploaded_files):
                with cols[idx % 4]:
                    st.image(img_file, caption=f"Imagen {idx + 1}", use_container_width=True)

        if st.button("Generar frontend", type="primary", disabled=len(uploaded_files) == 0):
            try:
                with st.spinner("Analizando capturas y generando archivos…"):
                    files_payload = [
                        ("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files
                    ]
                    resp = requests.post(API + "/projects", files=files_payload, timeout=180)
                    resp.raise_for_status()
                    st.session_state["project"] = resp.json()
                    st.session_state["original"] = [f.getvalue() for f in uploaded_files]
            except requests.RequestException as e:
                explain_error(e)

    else:
        url = st.text_input("URL pública", placeholder="https://example.com")
        st.info("No se admiten páginas privadas con login. Contenido dinámico puede no terminar de cargar y algunos sitios bloquean automatización o capturas.")
        if st.button("Capturar y generar", type="primary", disabled=not url.strip()):
            try:
                with st.spinner("Capturando la página y generando archivos…"):
                    resp = requests.post(API + "/projects/from-url", json={"url": url.strip()}, timeout=300)
                    resp.raise_for_status()
                    p = resp.json()
                    import base64
                    st.session_state["original"] = [base64.b64decode(p.pop("preview_image"))] if p.get("preview_image") else None
                    st.session_state["project"] = p
            except requests.RequestException as e:
                explain_error(e)

    project = st.session_state.get("project")
    if project:
        st.success(f"Proyecto {project['id']} guardado · {project['provider']} / {project['model']}")
        used_examples = project.get("dataset_examples", 0)
        if used_examples:
            st.caption(f"Generación contextualizada con {used_examples} referencia(s) del dataset WebSight.")
        else:
            st.caption("Para usar referencias del dataset, ejecuta el entrenamiento del notebook.")

        if "arbol_estructura" in project:
            st.markdown("### 📁 Estructura del Proyecto Recomendada")
            st.code(project["arbol_estructura"], language="text")

        left, right = st.columns(2)
        with left:
            st.subheader("Captura original")
            if st.session_state.get("original"):
                for idx, img_bytes in enumerate(st.session_state["original"]):
                    st.image(img_bytes, caption=f"Captura {idx + 1}", use_container_width=True)
        with right:
            st.subheader("Vista previa aislada")
            html_doc = '<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>' + project["css"] + '</style></head><body>' + project["html"] + ('<script>' + project.get("javascript", "") + '</script>' if project.get("javascript") else '') + '</body></html>'
            components.html('<iframe sandbox="allow-scripts" referrerpolicy="no-referrer" style="width:100%;height:650px;border:1px solid #ddd" srcdoc="' + html.escape(html_doc, quote=True) + '"></iframe>', height=670, scrolling=True)

        files = st.tabs(["HTML", "CSS", "JavaScript", "Estructura ASCII"])
        for t, key in zip(files, ["html", "css", "javascript", "arbol_estructura"]):
            with t:
                st.code(
                    project.get(key, "") or "(vacío)",
                    language={"html": "html", "css": "css", "javascript": "javascript", "arbol_estructura": "text"}[key],
                    line_numbers=True,
                    wrap_lines=True,
                )
        st.download_button("Descargar archivos (.zip)", bundle(project), file_name="reconstruccion_frontend.zip", mime="application/zip")

with tab_projects:
    if st.button("Actualizar proyectos"):
        try:
            r = requests.get(API + "/projects", timeout=10)
            r.raise_for_status()
            st.session_state["projects"] = r.json()
        except requests.RequestException as e:
            explain_error(e)
            
    for item in st.session_state.get("projects", []):
        with st.expander(f"{item['created_at']} · {item['source']} · {item['model']}"):
            a, b = st.columns([4, 1])
            with a:
                try:
                    r = requests.get(API + "/projects/" + item["id"], timeout=15)
                    r.raise_for_status()
                    p_detail = r.json()
                    if "arbol_estructura" in p_detail:
                        st.markdown("**Estructura del Proyecto:**")
                        st.code(p_detail["arbol_estructura"], language="text")
                    st.json(p_detail)
                except requests.RequestException as e:
                    explain_error(e)
            with b:
                if st.button("Eliminar", key="delete_" + item["id"]):
                    try:
                        r = requests.delete(API + "/projects/" + item["id"], timeout=10)
                        r.raise_for_status()
                        st.session_state["projects"] = [p for p in st.session_state.get("projects", []) if p["id"] != item["id"]]
                        st.rerun()
                    except requests.RequestException as e:
                        explain_error(e)