"""Shared loading of the saved model artefacts (used by the app, the API and the monitoring tools)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib

ROOT = Path(__file__).parent
MODEL_PATH = ROOT / "models/price_model.joblib"


def load_artifacts():
    """Return (model, defaults, info) exactly as the Streamlit app and the tests use them."""
    model = joblib.load(MODEL_PATH)
    defaults = json.loads((ROOT / "models/defaults.json").read_text())
    info = json.loads((ROOT / "reports/metrics.json").read_text())
    return model, defaults, info


def model_version() -> str:
    """Short fingerprint of the saved model file, so every logged prediction names the model that made it."""
    return hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()[:12]


APP_BASELINE_PATH = ROOT / "reports/app_input_holdout.json"


def load_app_baseline() -> dict | None:
    """Held-out accuracy of the app's 13-field form (python evaluate_app_inputs.py), or None if not measured yet."""
    if not APP_BASELINE_PATH.exists():
        return None
    return json.loads(APP_BASELINE_PATH.read_text())["app_13_inputs"]


def range_rmsle(info: dict) -> float:
    """Error size used for the 'typical range'. The form has less information than the full model, so its own error is used."""
    b = load_app_baseline()
    return b["rmsle"] if b else info["holdout_rmsle"]
