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
        try: st.error(exc.response.json().get("detail", str(exc)))
        except Exception: st.error(str(exc))
    else:
        st.error(f"No se pudo conectar con la API en {API}. Inicia FastAPI y revisa API_URL. Detalle: {exc}")


def bundle(project):
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.html", '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="styles.css"><title>Reconstrucción</title></head><body>\n' + project["html"] + '\n<script src="script.js"></script></body></html>')
        z.writestr("styles.css", project["css"])
        z.writestr("script.js", project.get("javascript", ""))
    return mem.getvalue()


tab_new, tab_projects = st.tabs(["Crear reconstrucción", "Proyectos guardados"])
with tab_new:
    mode = st.radio("Origen", ["Subir captura", "Capturar URL pública"], horizontal=True)
    if mode == "Subir captura":
        uploaded = st.file_uploader("Imagen JPG, PNG o WEBP (máximo 10 MB)", type=["jpg", "jpeg", "png", "webp"])
        if uploaded:
            st.image(uploaded, caption="Captura original", use_container_width=True)
        if st.button("Generar frontend", type="primary", disabled=uploaded is None):
            try:
                with st.spinner("Analizando la captura y generando archivos…"):
                    resp = requests.post(API + "/projects", files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}, timeout=120)
                    resp.raise_for_status(); st.session_state["project"] = resp.json(); st.session_state["original"] = uploaded.getvalue()
            except requests.RequestException as e: explain_error(e)
    else:
        url = st.text_input("URL pública", placeholder="https://example.com")
        st.info("No se admiten páginas privadas con login. Contenido dinámico puede no terminar de cargar y algunos sitios bloquean automatización o capturas.")
        if st.button("Capturar y generar", type="primary", disabled=not url.strip()):
            try:
                with st.spinner("Capturando la página y generando archivos…"):
                    resp = requests.post(API + "/projects/from-url", json={"url": url.strip()}, timeout=150)
                    resp.raise_for_status(); p = resp.json(); st.session_state["project"] = p
                    import base64
                    st.session_state["original"] = base64.b64decode(p.pop("preview_image")) if p.get("preview_image") else None
                    st.session_state["project"] = p
            except requests.RequestException as e: explain_error(e)
    project = st.session_state.get("project")
    if project:
        st.success(f"Proyecto {project['id']} guardado · {project['provider']} / {project['model']}")
        left, right = st.columns(2)
        with left:
            st.subheader("Captura original")
            if st.session_state.get("original"): st.image(st.session_state["original"], use_container_width=True)
        with right:
            st.subheader("Vista previa aislada")
            html_doc = '<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>' + project["css"] + '</style></head><body>' + project["html"] + ('<script>' + project.get("javascript", "") + '</script>' if project.get("javascript") else '') + '</body></html>'
            components.html('<iframe sandbox="allow-scripts" referrerpolicy="no-referrer" style="width:100%;height:650px;border:1px solid #ddd" srcdoc="' + html.escape(html_doc, quote=True) + '"></iframe>', height=670, scrolling=True)
        files = st.tabs(["HTML", "CSS", "JavaScript"])
        for t, key in zip(files, ["html", "css", "javascript"]):
            with t:
                st.code(
                    project.get(key, "") or "(vacío)",
                    language={"html": "html", "css": "css", "javascript": "javascript"}[key],
                    line_numbers=True,
                    wrap_lines=True,
                )
        st.download_button("Descargar archivos (.zip)", bundle(project), file_name="reconstruccion_frontend.zip", mime="application/zip")
with tab_projects:
    if st.button("Actualizar proyectos"):
        try:
            r = requests.get(API + "/projects", timeout=10); r.raise_for_status(); st.session_state["projects"] = r.json()
        except requests.RequestException as e: explain_error(e)
    for item in st.session_state.get("projects", []):
        with st.expander(f"{item['created_at']} · {item['source']} · {item['model']}"):
            a, b = st.columns([4, 1])
            with a:
                try:
                    r = requests.get(API + "/projects/" + item["id"], timeout=15); r.raise_for_status(); st.json(r.json())
                except requests.RequestException as e: explain_error(e)
            with b:
                if st.button("Eliminar", key="delete_" + item["id"]):
                    try:
                        r = requests.delete(API + "/projects/" + item["id"], timeout=10); r.raise_for_status(); st.session_state["projects"] = [p for p in st.session_state.get("projects", []) if p["id"] != item["id"]]; st.rerun()
                    except requests.RequestException as e: explain_error(e)
