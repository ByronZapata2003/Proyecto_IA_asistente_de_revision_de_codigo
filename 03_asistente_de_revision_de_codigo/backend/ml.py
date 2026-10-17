import joblib
from pathlib import Path
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

ART=Path(__file__).resolve().parents[1]/'models'/'modelo.joblib'
KIND=__import__('json').loads((Path(__file__).resolve().parents[1]/'config.json').read_text(encoding='utf8'))['tipo_modelo']

def train():
    ART.parent.mkdir(exist_ok=True)
    if KIND=='texto':
        texts=['error al iniciar sistema','fallo critico en produccion','incidencia de seguridad','servicio no disponible','solicitud de informacion','consulta de usuario','mejora de interfaz','peticion de nueva funcion']
        y=[1,1,1,1,0,0,0,0]
        m=make_pipeline(TfidfVectorizer(ngram_range=(1,2)),LogisticRegression(max_iter=1000))
        m.fit(texts,y)
    elif KIND=='regresion':
        rng=np.random.default_rng(42);X=rng.uniform(0,100,(160,3));y=2*X[:,0]+.5*X[:,1]-.2*X[:,2]+rng.normal(0,5,160)
        m=make_pipeline(StandardScaler(),Ridge());m.fit(X,y)
    else:
        rng=np.random.default_rng(42);X=rng.normal(0,1,(160,3));m=IsolationForest(random_state=42,contamination=.1);m.fit(X)
    joblib.dump(m,ART)
    return m

def predict(payload):
    m=joblib.load(ART) if ART.exists() else train()
    if KIND=='texto':
        v=str(payload.get('texto','')).strip()
        if not v:raise ValueError('Se requiere texto')
        result=int(m.predict([v])[0]);return {'prediccion':result,'etiqueta':'prioridad alta' if result else 'prioridad normal','nota':'Clasificador didactico con datos sinteticos'}
    vals=payload.get('valores',[])
    if not isinstance(vals,list) or len(vals)!=3:raise ValueError('Se requieren exactamente 3 valores numericos')
    try:x=np.asarray([vals],dtype=float)
    except (ValueError,TypeError):raise ValueError('Valores no numericos')
    if not np.isfinite(x).all():raise ValueError('Valores deben ser finitos')
    y=m.predict(x)[0]
    return {'prediccion':float(y) if KIND=='regresion' else int(y),'etiqueta':'estimacion' if KIND=='regresion' else ('normal' if y==1 else 'anomalia'),'nota':'Modelo demostrativo entrenado con datos sinteticos; no validado para produccion'}
