from backend.ml import train,predict,KIND
def test_model():
 train()
 assert 'prediccion' in predict({'texto':'error grave'} if KIND=='texto' else {'valores':[1,2,3]})
