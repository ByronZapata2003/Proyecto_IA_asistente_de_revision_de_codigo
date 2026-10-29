"""Descarga una muestra limitada del dataset WebSight en formato local."""

from pathlib import Path
import json
from datasets import load_dataset

ROOT=Path(__file__).resolve().parent
META=json.loads((ROOT/'dataset_fuente.json').read_text(encoding='utf-8'))
DATA=ROOT/'data'/'processed'

def download_dataset(max_samples=128, output_dir=DATA):
    """Obtiene hasta `max_samples` pares imagen/HTML sin descargar el corpus entero."""
    if max_samples < 1:
        raise ValueError('max_samples debe ser mayor que cero')

    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    manifest=output_dir/'examples.jsonl'
    dataset=load_dataset(
        META['repo'],
        name=META['configuracion'],
        split=META['split'],
        streaming=True,
    )

    written=0
    with manifest.open('w',encoding='utf-8') as output:
        for row in dataset:
            image=row.get('images') or row.get('image')
            html=row.get('text') or row.get('html')
            if image is None or not isinstance(html,str) or not html.strip():
                continue
            if not hasattr(image,'convert'):
                continue
            filename=f'{written:06d}.png'
            image.convert('RGB').save(output_dir/filename,format='PNG',optimize=True)
            record={
                'image':filename,
                'html':html,
                'description':str(row.get('llm_generated_idea','')),
            }
            output.write(json.dumps(record,ensure_ascii=False)+'\n')
            written+=1
            if written>=max_samples:
                break

    if not written:
        manifest.unlink(missing_ok=True)
        raise RuntimeError('No se encontraron pares imagen/HTML válidos en la muestra.')
    return {'samples':written,'manifest':manifest,'dataset':META['repo']}

def main():
    result=download_dataset()
    print(f"Dataset: {result['dataset']}")
    print(f"Pares guardados: {result['samples']}")
    print(f"Manifiesto: {result['manifest']}")
    print('La primera descarga puede transferir un shard grande aunque la muestra sea pequeña.')

if __name__=='__main__': main()
