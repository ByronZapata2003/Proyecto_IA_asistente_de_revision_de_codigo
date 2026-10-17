from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from datetime import datetime,timezone
from pathlib import Path
import os,json
from .ml import predict
load_dotenv(Path(__file__).resolve().parents[1]/'.env')
CFG=json.loads((Path(__file__).resolve().parents[1]/'config.json').read_text(encoding='utf8'))
app=FastAPI(title=CFG['titulo'])
class Input(BaseModel):
    texto:str|None=None
    valores:list[float]|None=None
    descripcion:str=Field(default='',max_length=500)
def collection():
    client=MongoClient(os.getenv('MONGO_URI','mongodb://localhost:27017'),serverSelectionTimeoutMS=3000)
    client.admin.command('ping')
    return client[os.getenv('MONGO_DB',CFG['db'])]['predicciones']
@app.get('/health')
def health():return {'estado':'api_activa','proyecto':CFG['titulo']}
@app.post('/predict')
def run(item:Input):
    try:r=predict(item.model_dump(exclude_none=True))
    except ValueError as e:raise HTTPException(422,str(e))
    doc={'entrada':item.model_dump(exclude_none=True),'resultado':r,'fecha':datetime.now(timezone.utc)}
    try:
        col=collection();saved=col.insert_one(doc);r['id']=str(saved.inserted_id)
    except PyMongoError as e:raise HTTPException(503,'MongoDB no disponible: '+str(e))
    return r
@app.get('/records')
def records(limit:int=20):
    if not 1<=limit<=200:raise HTTPException(422,'limit debe estar entre 1 y 200')
    try:
        docs=list(collection().find({},sort=[('fecha',-1)],limit=limit))
        for d in docs:d['_id']=str(d['_id']);d['fecha']=d['fecha'].isoformat()
        return docs
    except PyMongoError as e:raise HTTPException(503,'MongoDB no disponible: '+str(e))
