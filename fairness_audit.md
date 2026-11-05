# Fairness / responsible-AI audit (held-out homes)

Overall: 292 homes, median absolute error 5.2%, median signed error -0.5%.
Flags: median absolute error above 12%, or median signed error beyond ±5% (positive = over-estimate). Groups under 8 homes are not judged.

## By price band

| Group | Homes | Median abs. error | Median signed error | Within 15% | Status |
|---|---|---|---|---|---|
| Q1 cheapest | 73 | 6.3% | +1.4% | 73% | ok |
| Q2 | 73 | 3.7% | -0.7% | 93% | ok |
| Q3 | 73 | 5.0% | +0.8% | 92% | ok |
| Q4 most expensive | 73 | 6.0% | -3.5% | 92% | ok |

## By neighbourhood

| Group | Homes | Median abs. error | Median signed error | Within 15% | Status |
|---|---|---|---|---|---|
| IDOTRR | 7 | 17.2% | +17.2% | 43% | too few to judge |
| Blmngtn | 4 | 14.7% | -10.2% | 50% | too few to judge |
| OldTown | 23 | 11.0% | +2.9% | 70% | ok |
| ClearCr | 7 | 10.7% | -10.7% | 86% | too few to judge |
| SWISU | 6 | 7.8% | +7.0% | 83% | too few to judge |
| NoRidge | 7 | 7.2% | -4.4% | 86% | too few to judge |
| Crawfor | 12 | 6.7% | -4.2% | 67% | ok |
| NAmes | 37 | 6.2% | -0.9% | 86% | ok |
| MeadowV | 5 | 6.0% | +6.0% | 100% | too few to judge |
| SawyerW | 18 | 5.6% | -0.4% | 94% | ok |
| Edwards | 15 | 5.5% | -2.1% | 80% | ok |
| NridgHt | 12 | 5.4% | -1.5% | 100% | ok |
| Somerst | 22 | 5.3% | -3.3% | 95% | ok |
| BrDale | 5 | 5.2% | -0.0% | 100% | too few to judge |
| Gilbert | 13 | 4.6% | -1.9% | 92% | ok |
| BrkSide | 18 | 4.3% | -1.1% | 89% | ok |
| StoneBr | 3 | 4.2% | +4.2% | 67% | too few to judge |
| CollgCr | 38 | 4.0% | +0.6% | 95% | ok |
| Mitchel | 10 | 3.4% | -1.0% | 100% | ok |
| NWAmes | 9 | 3.3% | -1.6% | 89% | ok |
| Sawyer | 9 | 3.0% | -0.5% | 100% | ok |
| Timber | 11 | 2.7% | +1.7% | 100% | ok |
| Blueste | 1 | 0.1% | -0.1% | 100% | too few to judge |

## Reading this

- 0 of 18 judged groups are flagged: none.
- Not judged, but worth watching (large errors on fewer than 8 homes): IDOTRR (+17%, n=7), Blmngtn (-10%, n=4).
- Only 14 of 23 neighbourhoods have 8+ held-out homes, so the rest cannot be judged from this sample.
- Price bands are a fairness concern in their own right: if the cheapest homes are over-estimated, lower-income buyers and sellers bear the larger error.
- Before any real use, repeat this audit on a larger, more recent sample and add checks for the people and areas affected.
