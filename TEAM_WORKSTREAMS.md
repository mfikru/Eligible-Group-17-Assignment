# Team Workstreams (Module 6)

Nine members, nine workstreams. **This is a proposed split: edit it so it records what each person actually did, then copy the final table into the README.** Every member must also be able to explain the whole project (the assignment asks for this), so everyone reads the README first.

| Member | Workstream | Files to know | Show in the video | Be ready to explain |
| --- | --- | --- | --- | --- |
| Meron Mengesha | Streamlit app | `app.py` | Valid estimate, quality slider, invalid input, the "record real sale price" box, privacy note | Why requests are logged once per change; why the app shows two accuracy figures |
| Tenalem Temesgen Mesele | REST API | `api.py`, `tests/test_api.py` | `/docs` page, a valid call, a 422 error | Why 422 for bad input; same validation as the app |
| Ekram Yimam Mohammed | Experiment tracking | `reports/*.csv`, `log_to_mlflow.py`, `requirements-mlops.txt` | Results table; MLflow UI with 9 runs | What each log records; why CSV is the source of truth and MLflow a mirror |
| Hailemariam Moges | Testing and CI | `tests/`, `system_tests.py`, `.github/workflows/ci.yml` | 59 unit tests and 39 system tests passing; CI on GitHub | The neighbourhood validation bug the API exposed and how the tests catch it |
| Mezemir Birku Getie | Prediction log and accuracy monitoring | `prediction_log.py`, `monitoring.py` (accuracy), `evaluate_app_inputs.py` | A monitoring report with accuracy against real sale prices | Why the baseline is the form's accuracy (MAE $17,555), not the full model's |
| Nebiyu Arega Mulu | Data-drift monitoring | `monitoring.py` (drift), `models/reference_stats.json`, `simulate_traffic.py` | The SIMULATED drift report and its alerts | What PSI is and its thresholds; why the demo traffic is simulated and labelled |
| Mihret Fikru Minwalkulet | Responsible AI | `fairness_audit.py`, `reports/fairness_audit.md`, privacy design | The audit table and watch list | Why small groups cannot be judged; why neighbourhood needs care |
| Fami Abdi Mohammed | Deployment | `Dockerfile`, `Dockerfile.api`, `docker-compose.yml`, requirements files, GitHub and Streamlit hosting | `docker compose up --build`, public app link, GitHub repo | What is verified and what is not; why versions are pinned |
| Miftah Abdella Mohammed | Documentation and presentation | `README.md`, `docs/`, `CHANGELOG.md`, the video | Problem, solution and wrap-up | The implemented / simulated / future-work split; the data statement |

**Shared by everyone:** the model and data work from Module 5, the limitations, and one lesson learned each in the closing segment.

**Rule for the README table:** write what you did in your own words. If someone did not do their proposed workstream, change their line rather than submit a statement that is not true.
