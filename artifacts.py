"""Shared loading of the saved model artefacts (used by the app, the API and the monitoring tools)."""
from pathlib import Path
import joblib
import json

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "price_model.joblib"
DEFAULTS_PATH = BASE_DIR / "models" / "defaults.json"
INFO_PATH = BASE_DIR / "models" / "metrics.json"


def load_artifacts():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found: {MODEL_PATH}. "
            "Please upload price_model.joblib to the models folder."
        )

    model = joblib.load(MODEL_PATH)

    with open(DEFAULTS_PATH, "r") as f:
        defaults = json.load(f)

    with open(INFO_PATH, "r") as f:
        info = json.load(f)

    return model, defaults, info
