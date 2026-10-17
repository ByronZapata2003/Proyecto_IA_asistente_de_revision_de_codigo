import streamlit as st,requests,pandas as pd,os,json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1]/'.env')
cfg=json.loads((Path(__file__).resolve().parents[1]/'config.json').read_text(encoding='utf8'))
API=os.getenv('API_URL','http://127.0.0.1:8000')
st.set_page_config(page_title=cfg['titulo'],layout='wide',page_icon='🧠')
st.title('🧠 '+cfg['titulo']);st.caption('Curso de Inteligencia Artificial | Docente: Julian Rene Muñoz Burbano')
tab1,tab2,tab3=st.tabs(['Inferencia IA','Historial MongoDB','Acerca del modelo'])
with tab1:
    with st.form('inference'):
        if cfg['tipo_modelo']=='texto':
            payload={'texto':st.text_area('Ingrese un texto para clasificar','Error en el servidor de autenticacion')}
        else:
            st.info('Introduzca tres variables numericas de ejemplo. El modelo es un prototipo didactico.')
            cols=st.columns(3);payload={'valores':[cols[j].number_input(f'Variable {j+1}',value=float(j+1)) for j in range(3)]}
        payload['descripcion']=st.text_input('Descripcion opcional')
        submit=st.form_submit_button('Analizar y guardar',type='primary')
    if submit:
        try:
            r=requests.post(API+'/predict',json=payload,timeout=15);r.raise_for_status();st.success('Analisis registrado');st.json(r.json())
        except requests.RequestException as e:st.error(f'No se pudo completar: {e}')
with tab2:
    if st.button('Actualizar registros'):
        try:
            r=requests.get(API+'/records',timeout=10);r.raise_for_status();data=r.json();st.dataframe(pd.json_normalize(data),use_container_width=True)
            st.download_button('Exportar CSV',pd.json_normalize(data).to_csv(index=False).encode('utf-8-sig'),'registros.csv','text/csv')
        except requests.RequestException as e:st.error(str(e))
with tab3:
    st.write('Modelo:',cfg['tipo_modelo']);st.warning('Demostracion academica: datos sinteticos. Debe entrenarse y validarse con datos representativos antes de uso real.')
    st.code('http://127.0.0.1:8000/docs')
