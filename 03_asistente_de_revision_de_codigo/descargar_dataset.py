"""Obtención de datos. No descarga fuentes manuales sin confirmar términos de acceso."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parent
META=json.loads((ROOT/'dataset_fuente.json').read_text(encoding='utf-8'))
DATA=ROOT/'data'/'raw'
DATA.mkdir(parents=True,exist_ok=True)

def main():
    print('Dataset:', META['nombre'])
    print('Fuente:', META['url'])
    if META['modo']=='20news':
        from sklearn.datasets import fetch_20newsgroups
        ds=fetch_20newsgroups(subset='all',remove=('headers','footers','quotes'),data_home=str(ROOT/'data'/'cache'))
        out=DATA/'20newsgroups.csv'
        pd.DataFrame({'texto':ds.data,'categoria':[ds.target_names[i] for i in ds.target]}).to_csv(out,index=False)
        print('Descarga y exportación completadas:',out)
    else:
        print('Descarga manual o acceso condicionado. Consulte la URL, licencia y formato.')
        print('Guarde los archivos originales en:',DATA)
        print('No se generan datos sintéticos presentados como reales.')
if __name__=='__main__': main()
