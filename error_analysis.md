# Error analysis on the test split (scored once)

## By price quartile

| band              |   homes |   median_price |   median_abs_err_pct |   bias_pct |
|:------------------|--------:|---------------:|---------------------:|-----------:|
| Q1 cheapest       |      73 |         112000 |                  6.3 |        6.7 |
| Q2                |      73 |         140000 |                  3.7 |       -0.9 |
| Q3                |      73 |         187100 |                  5   |        1.8 |
| Q4 most expensive |      73 |         275000 |                  6   |       -3   |

## By neighbourhood (8+ test homes)

| Neighborhood   |   homes |   median_abs_err_pct |   bias_pct |
|:---------------|--------:|---------------------:|-----------:|
| OldTown        |      23 |                 11   |        6   |
| Crawfor        |      12 |                  6.7 |       -3.6 |
| NAmes          |      37 |                  6.2 |        1.3 |
| SawyerW        |      18 |                  5.6 |       -0.6 |
| Edwards        |      15 |                  5.5 |        1.6 |
| NridgHt        |      12 |                  5.4 |        0.1 |
| Somerst        |      22 |                  5.3 |       -2   |
| Gilbert        |      13 |                  4.6 |       -1.7 |
| BrkSide        |      18 |                  4.3 |        1.5 |
| CollgCr        |      38 |                  4   |        1.2 |
| Mitchel        |      10 |                  3.4 |       -1.9 |
| NWAmes         |       9 |                  3.3 |        1.5 |
| Sawyer         |       9 |                  3   |       -2.5 |
| Timber         |      11 |                  2.7 |        2   |

## Largest errors

| Neighborhood   |   GrLivArea |   OverallQual |   OverallCond |   YearBuilt | SaleCondition   |   SalePrice |     pred |   err_pct |
|:---------------|------------:|--------------:|--------------:|------------:|:----------------|------------:|---------:|----------:|
| IDOTRR         |        1317 |             4 |             4 |        1920 | Normal          |       40000 |  78822   |      97.1 |
| OldTown        |         968 |             4 |             6 |        1927 | Normal          |       64500 | 102706   |      59.2 |
| IDOTRR         |         480 |             2 |             3 |        1949 | Abnorml         |       35311 |  54487.9 |      54.3 |
| NAmes          |        2380 |             6 |             5 |        1965 | Abnorml         |      129000 | 177614   |      37.7 |
| NAmes          |        1776 |             5 |             5 |        1958 | Abnorml         |      110000 | 150531   |      36.8 |
| Edwards        |        1117 |             6 |             5 |        1976 | Abnorml         |      107000 | 145648   |      36.1 |
| OldTown        |        1131 |             4 |             7 |        1937 | Alloca          |       89471 | 115670   |      29.3 |
| BrkSide        |         935 |             5 |             6 |        1930 | Normal          |       79500 | 102710   |      29.2 |

## Top drivers (mean absolute effect on price, %)

|              |   mean_abs_effect_pct |
|:-------------|----------------------:|
| OverallQual  |                   6.5 |
| GrLivArea    |                   6.3 |
| TotalSF      |                   4.6 |
| HouseAge     |                   3.3 |
| OverallCond  |                   2.6 |
| TotalBath    |                   2.5 |
| LotArea      |                   2   |
| RemodAge     |                   1.8 |
| TotalBsmtSF  |                   1.7 |
| KitchenQual  |                   1.7 |
| GarageArea   |                   1.6 |
| Neighborhood |                   1.6 |
| ExterQual    |                   1.4 |
| GarageCars   |                   1.2 |
| BsmtFinSF1   |                   1.2 |
