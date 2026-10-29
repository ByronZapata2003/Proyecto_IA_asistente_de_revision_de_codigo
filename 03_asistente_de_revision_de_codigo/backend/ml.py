"""Índice visual k-NN entrenado con pares de capturas y HTML de WebSight."""

import json
from pathlib import Path

import joblib
import numpy as np
from PIL import Image
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
ARTIFACT = ROOT / "models" / "modelo.joblib"
IMAGE_SIZE = (32, 32)


def image_features(image):
    """Convierte una imagen PIL o una ruta a un vector RGB reproducible."""
    if isinstance(image, (str, Path)):
        with Image.open(image) as opened:
            image = opened.copy()
    if not isinstance(image, Image.Image):
        raise TypeError("La entrada debe ser una imagen PIL o una ruta de imagen.")
    thumbnail = image.convert("RGB").resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
    return np.asarray(thumbnail, dtype=np.float32).reshape(1, -1) / 255.0


def train(dataset_dir=DATA_DIR, artifact_path=ARTIFACT):
    """Ajusta un índice de vecinos sobre `examples.jsonl` y persiste el artefacto."""
    dataset_dir = Path(dataset_dir)
    manifest = dataset_dir / "examples.jsonl"
    if not manifest.is_file():
        raise FileNotFoundError(
            f"No existe {manifest}. Ejecuta descargar_dataset.py o la celda de descarga del notebook."
        )

    features, examples = [], []
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        image_name = row.get("image", "")
        html = row.get("html", "")
        image_path = dataset_dir / image_name
        if not image_path.is_file() or not isinstance(html, str) or not html.strip():
            continue
        try:
            features.append(image_features(image_path)[0])
        except (OSError, ValueError, TypeError) as exc:
            print(f"Omitiendo fila {line_number}: {type(exc).__name__}")
            continue
        examples.append(
            {
                "html": html[:200_000],
                "description": str(row.get("description", ""))[:1000],
                "image": image_name,
            }
        )

    if not examples:
        raise ValueError("El dataset no contiene pares válidos de imagen y HTML.")

    matrix = np.stack(features)
    index = NearestNeighbors(metric="cosine", algorithm="brute")
    index.fit(matrix)
    model = {
        "index": index,
        "features": matrix,
        "examples": examples,
        "image_size": IMAGE_SIZE,
        "dataset": "HuggingFaceM4/WebSight v0.2",
    }
    artifact_path = Path(artifact_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_path)
    return model


def is_trained(artifact_path=ARTIFACT):
    return Path(artifact_path).is_file()


def retrieve_examples(image, limit=2, artifact_path=ARTIFACT):
    """Busca pares visualmente cercanos para usarlos como generación contextual."""
    artifact_path = Path(artifact_path)
    if not artifact_path.is_file():
        return []
    model = joblib.load(artifact_path)
    count = min(max(int(limit), 1), len(model["examples"]))
    distances, indices = model["index"].kneighbors(image_features(image), n_neighbors=count)
    results = []
    for distance, index in zip(distances[0], indices[0]):
        results.append({**model["examples"][int(index)], "distance": float(distance)})
    return results
