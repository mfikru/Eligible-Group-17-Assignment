"""Shared loading of the saved model artefacts (used by the app, the API and the monitoring tools).

Each file is looked for in its usual folder (models/ or reports/) and then in the project root, so the project also
works when all files sit in one folder.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib

ROOT = Path(__file__).parent


def _find(name: str, folder: str, required: bool = True) -> Path | None:
    for p in (ROOT / folder / name, ROOT / name):
        if p.is_file():
            return p
    if required:
        raise FileNotFoundError(
            f"Required file '{name}' was not found (looked in '{folder}/' and in the project root). "
            "Upload the complete project files.")
    return None


def _check_metrics(info: dict) -> None:
    """metrics.json must be the real evaluation file written by train.py, not a placeholder."""
    ok = (isinstance(info.get("holdout_rmsle"), (int, float)) and isinstance(info.get("targets_vs_achieved"), dict)
          and "chosen_model" in info)
    if not ok:
        raise ValueError(
            "metrics.json is not the real model evaluation file (it has no 'holdout_rmsle' / 'targets_vs_achieved'). "
            "Use the metrics.json that came with the project (reports/metrics.json); do not create or edit it by hand.")


def load_artifacts():
    """Return (model, defaults, info) exactly as the Streamlit app and the tests use them."""
    model = joblib.load(_find("price_model.joblib", "models"))
    defaults = json.loads(_find("defaults.json", "models").read_text(encoding="utf-8"))
    info = json.loads(_find("metrics.json", "reports").read_text(encoding="utf-8"))
    _check_metrics(info)
    return model, defaults, info


def model_version() -> str:
    """Short fingerprint of the saved model file, so every logged prediction names the model that made it."""
    return hashlib.sha256(_find("price_model.joblib", "models").read_bytes()).hexdigest()[:12]


def load_app_baseline() -> dict | None:
    """Held-out accuracy of the app's 13-field form (python evaluate_app_inputs.py), or None if not measured yet."""
    p = _find("app_input_holdout.json", "reports", required=False)
    return json.loads(p.read_text(encoding="utf-8"))["app_13_inputs"] if p else None


def range_rmsle(info: dict) -> float:
    """Error size used for the 'typical range'. The form has less information than the full model, so its own error is used."""
    b = load_app_baseline()
    return b["rmsle"] if b else info["holdout_rmsle"]
