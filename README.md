# House Price Estimator: Group 17

FUSE AI-201 · Module 6: AI Deployment, Monitoring, Support & Maintenance

**Group members and responsibilities:** [Name: e.g. data prep & modelling] · [Name: e.g. MLflow & testing] · [Name: e.g. app & documentation]
**Links:** GitHub: [URL] · Streamlit app: [URL or "not public; see screenshots in docs/evidence/"] · Video: submitted on Canvas

## Purpose
Estimate the sale price of a residential house from its characteristics, as a decision aid for
valuation/real-estate screening. *(Align this paragraph with your Module 4 proposal.)*
It is a **prototype**, not a production valuation system.

## Data (see Deliverable D)
Real, public **Kaggle Ames Housing** data: 1,460 training rows, 79 features, target `SalePrice`.
No simulated data is used for training or evaluation. Synthetic data appears only in `tests/` to check the code runs.

## How it fits together
```
train.csv ─► src/train.py ─► preprocessing (impute + one-hot) ─► Linear Regression / Random Forest
                │                      (target log1p-transformed)
                ├─► MLflow (params, metrics, model per run)
                └─► models/best_model.joblib + models/metadata.json
                                     │
                    ┌────────────────┴────────────────┐
                 app.py (Streamlit)              api.py (FastAPI)
                    └── src/validation.py ── src/predict.py ──► logs/predictions.csv ─► monitoring/monitor.py
```

## Results (20% held-out validation split of 292 houses, `random_state=42`; reproduced by `src/train.py` and the notebook on the real Ames `train.csv`)
| Model | RMSLE ↓ | RMSE ($) | MAE ($) | R² |
|---|---|---|---|---|
| **Linear Regression (log target)** | **0.1419** | 25,418 | 16,970 | 0.916 |
| Random Forest (300 trees) | 0.1453 | 29,705 | 17,365 | 0.885 |

Linear Regression won on every metric, so it is the model the app uses. These numbers describe
historical Ames sales in a single split, **not** live performance. Linear Regression matches the original Module 5 notebook; the original Random Forest scored slightly differently (RMSLE 0.1452, RMSE 28,880), so its settings differed from the 300-tree forest used here.

## Setup and run
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 1. put Kaggle train.csv in data/
python -m src.train --data data/train.csv               # trains, logs to MLflow, saves models/ (a trained model is already included)
streamlit run app.py                                    # demo UI  -> http://localhost:8501
uvicorn api:app --reload                                # optional API -> http://localhost:8000/docs
mlflow ui --backend-store-uri sqlite:///mlflow.db       # view experiments -> http://localhost:5000
pytest -q                                               # 25 tests (use synthetic data)
python -m monitoring.monitor --log logs/predictions.csv # monitoring report
```
Docker (optional): see the header of `Dockerfile`.

### Example API call (returns about $183,393, range $159k-$211k, on the trained model)
```bash
curl -X POST localhost:8000/predict -H "Content-Type: application/json" -d '{
 "OverallQual":7,"GrLivArea":1800,"TotalBsmtSF":900,"GarageCars":2,"FullBath":2,
 "BedroomAbvGr":3,"YearBuilt":2003,"YearRemodAdd":2003,"LotArea":9600,"Neighborhood":"CollgCr"}'
```

## Input checks and error handling
`src/validation.py` rejects missing fields, wrong types, NaN/inf, out-of-range values, unknown
neighborhoods and remodel-before-built years (errors), and warns when a value is valid but outside
the training range. Unexpected failures are logged to `logs/app.log` and the user sees a safe message.

## Project map
| Path | Purpose |
|---|---|
| `src/` | config, validation, pipeline, training, prediction |
| `app.py`, `api.py` | Streamlit UI, FastAPI service |
| `monitoring/monitor.py` | drift (PSI), data quality, live accuracy check |
| `tests/` | pytest suite (synthetic data) |
| `docs/` | monitoring plan, testing evidence, limitations, retrospective, data statement, checklist |
| `notebooks/module_6.ipynb` | cleaned, reproducible notebook (MLflow tracking); `module_6_original.ipynb` keeps the earlier version |

## Limitations
See `docs/LIMITATIONS.md`. In short: Ames, Iowa 2006-2010 only; the app asks for 10 of 79 features and fills the rest with typical values; no fairness audit; not a professional valuation.

## Security
No keys, credentials or personal data are stored. Prediction logs contain only the 10 property fields, a timestamp and the estimate.
