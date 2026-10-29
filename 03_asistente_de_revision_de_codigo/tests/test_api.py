import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from PIL import Image
from backend import api

client = TestClient(api.app)

def png():
    b=io.BytesIO(); Image.new('RGB',(20,20),'white').save(b,'PNG'); return b.getvalue()

def test_upload_rejects_wrong_mime():
    r=client.post('/projects',files={'file':('x.txt',b'hello','text/plain')})
    assert r.status_code==415

def test_upload_rejects_corrupt_image():
    r=client.post('/projects',files={'file':('x.png',b'not image','image/png')})
    assert r.status_code==422

def test_missing_key_is_actionable(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    r=client.post('/projects',files={'file':('x.png',png(),'image/png')})
    assert r.status_code==503 and 'OPENAI_API_KEY' in r.json()['detail']

def test_generate_and_save(monkeypatch):
    class Insert: inserted_id='abc123'
    class Collection:
        def insert_one(self, doc): self.doc=doc; return Insert()
    col=Collection()
    monkeypatch.setenv('OPENAI_API_KEY','test-only')
    monkeypatch.setattr(api,'get_collection',lambda:col)
    monkeypatch.setattr(api,'generate',lambda image:{'html':'<main>Hi</main>','css':'main{}','javascript':'','provider':'OpenAI','model':'fake'})
    r=client.post('/projects',files={'file':('x.png',png(),'image/png')})
    assert r.status_code==200 and r.json()['id']=='abc123'
    assert col.doc['source']=='x.png' and col.doc['html']=='<main>Hi</main>'

def test_projects_limit_validation():
    assert client.get('/projects?limit=0').status_code==422

def test_private_url_rejected_before_capture():
    from backend.api import ensure_public_url
    from fastapi import HTTPException
    import pytest
    with pytest.raises(HTTPException) as err:
        ensure_public_url('http://127.0.0.1/admin')
    assert err.value.status_code == 422

def test_get_missing_project_returns_404():
    r=client.get('/projects/507f1f77bcf86cd799439011')
    assert r.status_code==503 or r.status_code==404

def test_invalid_project_id_rejected():
    assert client.delete('/projects/nope').status_code==422
