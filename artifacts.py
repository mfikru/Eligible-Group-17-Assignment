"""Shared loading of the saved model artefacts (used by the app, the API and the monitoring tools)."""
from pathlib import Path
import joblib
import json

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "price_model.joblib"
DEFAULTS_PATH = BASE_DIR / "defaults.json"
INFO_PATH = BASE_DIR / "metrics.json"
print("Project directory:", BASE_DIR)
print("Model path:", MODEL_PATH)
print("Model exists:", MODEL_PATH.exists())
print("Model file size:", MODEL_PATH.stat().st_size if MODEL_PATH.exists() else "MISSING")

def load_artifacts():

    for path in [MODEL_PATH, DEFAULTS_PATH, INFO_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

    model = joblib.load(MODEL_PATH)

    with open(DEFAULTS_PATH, encoding="utf-8") as f:
        defaults = json.load(f)

    with open(INFO_PATH, encoding="utf-8") as f:
        info = json.load(f)

    return model, defaults, info
