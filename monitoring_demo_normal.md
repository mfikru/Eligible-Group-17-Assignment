# SIMULATED monitoring demo: normal scenario

> **SIMULATED DATA.** Replayed held-out homes. Not evidence of real-world performance. The model had seen these homes in training.

## Operations

- Requests: **200** (0% rejected as invalid, 1% of accepted ones carried a warning)
- Sources: {'simulated': 200}; model versions: {'71f8adf058d4': 200}
- Response time: median 125 ms, 95th percentile 251 ms

## Data drift (PSI: below 0.10 stable, 0.10 to 0.25 moderate, above 0.25 significant)

| Feature | PSI | Status |
|---|---|---|
| GrLivArea | 0.021 | stable |
| LotArea | 0.047 | stable |
| TotalBsmtSF | 0.026 | stable |
| YearBuilt | 0.058 | stable |
| OverallQual | 0.015 | stable |
| GarageCars | 0.006 | stable |
| Neighborhood | 0.207 | moderate |
| Predicted price | 0.066 | stable |

## Accuracy against real sale prices

| Metric | Now | Baseline |
|---|---|---|
| MAE | $17,045 | $17,555 |
| RMSLE | 0.123 | 0.140 |
| Within 15% of actual | 78% | 78% |
| Typical range coverage | 74% | 76% |
| Median bias | -2.7% | |

Based on 200 estimates with a known sale price. Baseline: 13-field form on held-out homes.

## Alerts

None.
