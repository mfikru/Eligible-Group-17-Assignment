"""Prediction log (SQLite) for monitoring and support.

What is stored: the form inputs, the estimate and range, warnings/errors, the model version and the response time.
What is NOT stored: names, addresses, IP addresses or any other personal data. The app has no such fields.

Switch off with the environment variable PRICE_LOG=0. Change the location with PRICE_LOG_DB (default logs/predictions.db).
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    request_id TEXT PRIMARY KEY, ts TEXT NOT NULL, source TEXT NOT NULL, ok INTEGER NOT NULL,
    inputs TEXT NOT NULL, price REAL, low REAL, high REAL, warnings TEXT, errors TEXT,
    model_version TEXT, latency_ms REAL
);
CREATE TABLE IF NOT EXISTS outcomes (
    request_id TEXT PRIMARY KEY, actual_price REAL NOT NULL, ts TEXT NOT NULL
);
"""


def logging_enabled() -> bool:
    return os.environ.get("PRICE_LOG", "1") != "0"


def db_path() -> Path:
    return Path(os.environ.get("PRICE_LOG_DB", ROOT / "logs/predictions.db"))


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p, timeout=10)
    con.executescript(SCHEMA)
    return con


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_prediction(inputs: dict, out: dict, *, source: str, model_version: str = "", latency_ms: float | None = None,
                   path: Path | None = None) -> str | None:
    """Record one request. Returns its request_id (None if logging is off or fails: logging never breaks the app)."""
    if not logging_enabled():
        return None
    rid = uuid.uuid4().hex[:12]
    res = out.get("result") or {}
    try:
        with closing(_connect(path)) as con, con:
            con.execute(
                "INSERT INTO predictions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (rid, _now(), source, int(bool(out.get("ok"))), json.dumps(inputs, default=str, sort_keys=True),
                 res.get("price"), res.get("low"), res.get("high"), json.dumps(out.get("warnings", [])),
                 json.dumps(out.get("errors", [])), model_version, latency_ms),
            )
        return rid
    except sqlite3.Error:
        return None


def log_outcome(request_id: str, actual_price: float, path: Path | None = None) -> bool:
    """Attach the real sale price to an earlier estimate. Returns False if the id is unknown or the price is invalid."""
    try:
        price = float(actual_price)
    except (TypeError, ValueError):
        return False
    if not (price > 0) or price == float("inf"):
        return False
    with closing(_connect(path)) as con, con:
        if con.execute("SELECT 1 FROM predictions WHERE request_id=? AND ok=1", (request_id,)).fetchone() is None:
            return False
        con.execute("INSERT OR REPLACE INTO outcomes VALUES (?,?,?)", (request_id, price, _now()))
    return True


def read_log(path: Path | None = None) -> pd.DataFrame:
    """All logged requests with the actual price (NaN until known). Inputs are expanded into columns."""
    with closing(_connect(path)) as con:
        df = pd.read_sql_query(
            "SELECT p.*, o.actual_price FROM predictions p LEFT JOIN outcomes o USING(request_id) ORDER BY ts", con)
    if df.empty:
        return df
    inputs = pd.json_normalize(df["inputs"].map(json.loads))
    return pd.concat([df.drop(columns=["inputs"]), inputs], axis=1)
