# SIMULATED monitoring demo: drift scenario

> **SIMULATED DATA.** Replayed held-out homes with an invented market change. Not evidence of real-world performance. The model had seen these homes in training.

## Operations

- Requests: **200** (0% rejected as invalid, 0% of accepted ones carried a warning)
- Sources: {'simulated': 200}; model versions: {'71f8adf058d4': 200}
- Response time: median 138 ms, 95th percentile 231 ms

## Data drift (PSI: below 0.10 stable, 0.10 to 0.25 moderate, above 0.25 significant)

| Feature | PSI | Status |
|---|---|---|
| GrLivArea | 1.236 | significant |
| LotArea | 0.112 | moderate |
| TotalBsmtSF | 0.233 | moderate |
| YearBuilt | 1.818 | significant |
| OverallQual | 1.897 | significant |
| GarageCars | 0.350 | significant |
| Neighborhood | 1.272 | significant |
| Predicted price | 1.032 | significant |

## Accuracy against real sale prices

| Metric | Now | Baseline |
|---|---|---|
| MAE | $54,492 | $17,555 |
| RMSLE | 0.217 | 0.140 |
| Within 15% of actual | 44% | 78% |
| Typical range coverage | 30% | 76% |
| Median bias | -16.4% | |

Based on 200 estimates with a known sale price. Baseline: 13-field form on held-out homes.

## Alerts

- Significant drift in GrLivArea (PSI 1.24).
- Significant drift in YearBuilt (PSI 1.82).
- Significant drift in OverallQual (PSI 1.90).
- Significant drift in GarageCars (PSI 0.35).
- Significant drift in Neighborhood (PSI 1.27).
- Significant drift in Predicted price (PSI 1.03).
- MAE $54,492 is more than 20% above the baseline $17,555.
- Only 44% of estimates are within 15% of the actual price (baseline 78%, alert below 68%).
- The typical range holds only 30% of actual prices (baseline 76%): recalibrate it.

Action: review the data and consider retraining (see the maintenance plan, section 3).
