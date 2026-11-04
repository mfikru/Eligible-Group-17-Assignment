"""Shared loading of the saved model artefacts (used by the app, the API and the monitoring tools)."""
from pathlib import Path
import hashlib
import json
import joblib

ROOT = Path(__file__).resolve().parent

# All three files are in the project root
MODEL_PATH = ROOT / "price_model.joblib"
DEFAULTS_PATH = ROOT / "defaults.json"
METRICS_PATH = ROOT / "metrics.json"

# Optional evaluation report
APP_BASELINE_PATH = ROOT / "reports" / "app_input_holdout.json"


def load_artifacts():
    """Load model, defaults and evaluation information."""

    required_files = [
        MODEL_PATH,
        DEFAULTS_PATH,
        METRICS_PATH
    ]

    for path in required_files:
        if not path.is_file():
            raise FileNotFoundError(
                f"Required artifact is missing: {path}"
            )

    model = joblib.load(MODEL_PATH)

    with open(DEFAULTS_PATH, "r", encoding="utf-8") as f:
        defaults = json.load(f)

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        info = json.load(f)

    return model, defaults, info


def model_version():
    """Return a short model fingerprint."""
    return hashlib.sha256(
        MODEL_PATH.read_bytes()
    ).hexdigest()[:12]


def load_app_baseline():
    """Load optional app evaluation results."""
    if not APP_BASELINE_PATH.exists():
        return None

    data = json.loads(
        APP_BASELINE_PATH.read_text(encoding="utf-8")
    )

    return data["app_13_inputs"]


def range_rmsle(info):
    """Return the appropriate prediction-range error."""
    baseline = load_app_baseline()

    if baseline:
        return baseline["rmsle"]

    return info["holdout_rmsle"]
