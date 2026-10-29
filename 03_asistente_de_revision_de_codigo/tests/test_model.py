import json

from PIL import Image

from backend.ml import is_trained, retrieve_examples, train


def test_training_indexes_real_image_html_pairs(tmp_path):
    Image.new("RGB", (64, 40), "#2457a6").save(tmp_path / "sample.png")
    (tmp_path / "examples.jsonl").write_text(
        json.dumps({"image": "sample.png", "html": "<main>Web</main>"}) + "\n",
        encoding="utf-8",
    )
    artifact = tmp_path / "modelo.joblib"

    model = train(tmp_path, artifact)
    result = retrieve_examples(Image.new("RGB", (64, 40), "#2457a6"), artifact_path=artifact)

    assert is_trained(artifact)
    assert len(model["examples"]) == 1
    assert result[0]["html"] == "<main>Web</main>"
    assert result[0]["distance"] < 1e-7


def test_training_requires_a_dataset_manifest(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError, match="examples.jsonl"):
        train(tmp_path, tmp_path / "modelo.joblib")
