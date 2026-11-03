# Home Price Estimator (Ames, Iowa)

**FUSE AI-201 · Group 17 · Real Estate / Housing Market Analytics**
Module 4 proposal → Module 5 implementation → **Module 6: demonstration, deployment and maintenance**

| Item | Link |
| --- | --- |
| GitHub repository | `[ADD LINK]` |
| Live Streamlit app | `[ADD LINK, or "run locally, see section 6"]` |
| Demo video | Submitted on Canvas |

## 1. What it does
Estimates a home's sale price from 13 inputs (neighbourhood, living area, quality, year built, garage, and so on), shows a typical-error range and the main drivers of the estimate, and rejects bad input with a message that names the faulty field. It is available as a **Streamlit app** and a **REST API**. Every request can be logged (no personal data) so accuracy and data drift can be monitored.
**It is an estimate, not an appraisal, and not for lending decisions.**

## 2. Data
Real, non-simulated data: the Kaggle *House Prices: Advanced Regression Techniques* (Ames Housing) training file, 1,460 homes, sales 2006–2010 (De Cock, 2011); two outliers removed, 1,458 used. The file is not redistributed (`data/README.md`). The only simulated data are the **monitoring demo traffic** in section 8, which is clearly labelled. Full statement: `docs/SIMULATED_DATA_STATEMENT.md`.

## 3. Results
Final model: equal average of Lasso and LightGBM, trained on log price. Model selection used 5-fold cross-validation on 80% of homes; the other 20% (292 homes) was scored once.

| Model (cross-validation) | CV RMSLE | CV MAE | CV R² |
| --- | --- | --- | --- |
| Baseline A: median price | 0.3972 | $55,326 | -0.055 |
| Baseline B: linear regression | 0.1658 | $21,392 | 0.854 |
| Lasso | 0.1121 | $14,028 | 0.926 |
| Random Forest (tuned) | 0.1307 | $16,252 | 0.891 |
| LightGBM (tuned) | 0.1151 | $14,161 | 0.920 |
| **Lasso 0.5 + LightGBM 0.5** | **0.1089** | **$13,315** | **0.930** |

**Held-out homes (scored once), two ways:**

| | RMSLE | MAE | Within 15% of actual | Typical range holds |
| --- | --- | --- | --- | --- |
| All 79 features (`reports/metrics.json`) | 0.111 | $13,236 | 87.3% | 76% (±11%) |
| **Through the app's 13-field form** (`reports/app_input_holdout.json`) | 0.140 | $17,555 | 78.1% | 76% (±14%) |

The form has less information than the full model, so it is less accurate; the Module 5 figures describe the full-feature model. The 78% misses the proposal's 80% target, while the 87% met it. Reproduce with `python evaluate_app_inputs.py` (it retrains the 80% model in memory and leaves the saved model untouched). With the original ±11% range, only 65% of held-out homes fell inside it through the form, so the app now uses ±14%.

## 4. What changed in Module 6
See `CHANGELOG.md`. In short: prediction logging and a feedback box (app), `api.py` REST API, `monitoring.py` (drift, accuracy, operations), `fairness_audit.py`, `evaluate_app_inputs.py`, `log_to_mlflow.py`, `simulate_traffic.py`, stricter neighbourhood validation, 40 new unit tests and 8 new system tests, Docker/compose files for the app and API, and a CI workflow.

## 5. Implemented, simulated, or future work
| Status | Item |
| --- | --- |
| Implemented | Model, Streamlit app, REST API, validation, prediction log, feedback box, drift/accuracy/operations report, fairness audit, MLflow mirror of the experiment logs, unit and system tests, Docker files, CI workflow |
| Simulated (labelled) | Monitoring-demo traffic (`simulate_traffic.py`): replayed held-out homes, and an invented market shift |
| Not yet verified | `docker compose up --build` (files written; build once and screenshot it), a public Streamlit URL, CI run on GitHub |
| Future work | Retrain on recent local sales, scheduled monitoring (cron/Actions), alert delivery (email/Slack), authentication and rate limiting for a public API, a larger fairness audit, richer inputs |

## 6. Run it
Python 3.12; pinned versions in the requirements files (the saved model must load with the same scikit-learn, LightGBM and pandas).

```bash
pip install -r requirements-api.txt        # app + API (requirements.txt is app/training only)
streamlit run app.py                       # app on http://localhost:8501
uvicorn api:app --port 8000                # API; interactive docs at http://localhost:8000/docs
python -m pytest tests -q                  # unit tests
python system_tests.py                     # whole-system tests -> reports/system_tests.csv
```
Retraining from scratch needs `data/train.csv` from Kaggle: `python experiments.py` → `python train.py`.
Docker: `docker compose up --build` (app :8501, API :8000, shared log volume). No keys, passwords or credentials are used anywhere.

**API example**
```bash
curl -X POST localhost:8000/predict -H "content-type: application/json" -d '{"Neighborhood":"NAmes","GrLivArea":1500,"Stories":1,"LotArea":9000,"OverallQual":6,"OverallCond":5,"YearBuilt":1975,"YearRemodAdd":1990,"GarageCars":2,"TotalBsmtSF":900,"FullBath":2,"HalfBath":0,"KitchenQual":"TA"}'
```
returns `price`, `low`, `high`, `drivers`, `warnings` and a `request_id`; invalid input returns **422** with the error messages. `POST /outcome {"request_id", "actual_price"}` records the real sale price. `GET /health`, `GET /model-info`.

## 7. Testing (verified before this README was written)
| Suite | Command | Result |
| --- | --- | --- |
| Unit and API tests | `python -m pytest tests -q` | 59 passed (19 from Module 5, 40 new) |
| Whole-system tests | `python system_tests.py` | 39 of 39 pass (`reports/system_tests.csv`): normal, missing, invalid, unexpected category, extreme, model behaviour, API, performance (0.13 s per estimate), whole app |

Add screenshots to `screenshots/`: valid estimate, invalid-input error, API `/docs`, passing tests, monitoring report, MLflow UI.

## 8. Experiment tracking, monitoring and responsible AI
| What | How |
| --- | --- |
| Experiment logs | CSV/JSON in `reports/` and `models/best_params.json` (source of truth) |
| MLflow | `pip install -r requirements-mlops.txt && python log_to_mlflow.py && mlflow ui --backend-store-uri sqlite:///mlflow.db` (9 runs: 8 candidates + final) |
| Prediction log | `logs/predictions.db` (SQLite): inputs, estimate, range, warnings, model version, response time. Off with `PRICE_LOG=0` |
| Monitoring report | `python monitoring.py report` → `reports/monitoring_report.md`; exits non-zero when an alert fires |
| Fairness audit | `python fairness_audit.py` → `reports/fairness_audit.md` |
| Monitoring demo | `python simulate_traffic.py --scenario normal` or `drift` → `reports/monitoring_demo_*.md` |

**Monitoring demo (SIMULATED, not real-world evidence):** replaying 200 held-out homes raises no alerts (MAE $17,045 vs baseline $17,555). An invented market shift (bigger, newer homes, prices 40% higher) raises 9 alerts: six measures (five inputs and the predicted price) drifted significantly (PSI above 0.25), MAE rises to $54,492, and only 44% of estimates are within 15%.
**Fairness audit (held-out homes):** none of the 18 groups with 8+ homes is flagged. OldTown (11.0% median error) is closest to the 12% threshold. IDOTRR (+17% over-estimate, 7 homes) and Blmngtn (−10%, 4 homes) have too few homes to judge and are on a watch list.
Details: `docs/MONITORING_SUPPORT_MAINTENANCE_PLAN.md`.

## 9. Limitations
- Homes are valued as of 2010 and only in Ames; prices have changed since.
- The 13-field form is less accurate than the full-feature model (section 3).
- Random Forest and LightGBM fit training data about three times tighter than new data, so Lasso is blended in; the ensemble's gain over Lasso alone is small (CV RMSLE 0.109 vs 0.112).
- Largest errors: cheap, older homes and unusual sales such as foreclosures, which the model cannot see (`reports/error_analysis.md`).
- The fairness audit uses 292 homes; most neighbourhoods have too few to judge.
- An early Module 5 prototype printed test scores before the workflow was fixed; no choice was based on them, but the test sample is slightly less pristine.
- Replayed monitoring traffic uses a model that was trained on those homes, so it is optimistic.

## 10. Group members and responsibilities
Nine members; see `docs/TEAM_WORKSTREAMS.md` for the proposed split of the Module 6 work. **Each member must check and edit their own line to match what they actually did.**

| Member | Responsibility (confirm or edit) |
| --- | --- |
| Meron Mengesha | Streamlit app: logging, feedback box, privacy note |
| Tenalem Temesgen Mesele | REST API |
| Arega Mulu Mezemir| Data-drift monitoring |
| Nebiyu| Data-drift monitoring |
| Birku Getie Mihret | Prediction log and accuracy monitoring |
| Fikru Minwalkulet Workneh| Fairness audit and responsible AI |
| Hailemariam Moges | Testing and CI |
| Ekram Yimam Mohammed | Experiment tracking (CSV logs, MLflow) |
| Fami Abdi Mohammed | Deployment (Docker, GitHub, Streamlit hosting) |
| Miftah Abdella Mohammed | Documentation, retrospective and video |

## 11. References
- De Cock, D. (2011). *Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project.* Journal of Statistics Education.
- Kaggle, *House Prices: Advanced Regression Techniques*: https://www.kaggle.com/c/house-prices-advanced-regression-technique
