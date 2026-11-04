"""Shared code for the Ames house-price estimator.

Used by train.py (training and evaluation), app.py (Streamlit app) and the tests,
so that training and serving always apply identical preprocessing.

Contents
    AmesPreprocessor  - cleaning, feature engineering, encoding (fitted on training data only)
    PriceModel        - Lasso + LightGBM average with additive per-feature contributions
    compute_defaults  - neighbourhood-level typical values used to fill fields the user does not enter
    build_row         - turn the ~11 app inputs into a full 79-column row
    estimate          - price, typical-error range and top drivers for one home
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.stats import skew
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler

# --------------------------------------------------------------------------- #
# Column groups
# --------------------------------------------------------------------------- #
# In these columns NA means "the house has no such feature", not "missing".
NONE_CATS = [
    "Alley", "BsmtQual", "BsmtCond", "BsmtExposure", "BsmtFinType1", "BsmtFinType2",
    "FireplaceQu", "GarageType", "GarageFinish", "GarageQual", "GarageCond",
    "PoolQC", "Fence", "MiscFeature", "MasVnrType",
]
# Numeric columns where NA means the feature is absent (zero).
ZERO_NUMS = [
    "MasVnrArea", "BsmtFinSF1", "BsmtFinSF2", "BsmtUnfSF", "TotalBsmtSF",
    "BsmtFullBath", "BsmtHalfBath", "GarageCars", "GarageArea",
]
QUAL = {"None": 0, "Po": 1, "Fa": 2, "TA": 3, "Gd": 4, "Ex": 5}
QUAL_COLS = [
    "ExterQual", "ExterCond", "BsmtQual", "BsmtCond", "HeatingQC",
    "KitchenQual", "FireplaceQu", "GarageQual", "GarageCond", "PoolQC",
]
BSMT_FIN = {"None": 0, "Unf": 1, "LwQ": 2, "Rec": 3, "BLQ": 4, "ALQ": 5, "GLQ": 6}
ORDINALS = {c: QUAL for c in QUAL_COLS}
ORDINALS.update({
    "BsmtExposure": {"None": 0, "No": 1, "Mn": 2, "Av": 3, "Gd": 4},
    "BsmtFinType1": BSMT_FIN,
    "BsmtFinType2": BSMT_FIN,
    "GarageFinish": {"None": 0, "Unf": 1, "RFn": 2, "Fin": 3},
    "Functional": {"Sal": 0, "Sev": 1, "Maj2": 2, "Maj1": 3, "Mod": 4, "Min2": 5, "Min1": 6, "Typ": 7},
    "LotShape": {"IR3": 0, "IR2": 1, "IR1": 2, "Reg": 3},
    "LandSlope": {"Sev": 0, "Mod": 1, "Gtl": 2},
    "PavedDrive": {"N": 0, "P": 1, "Y": 2},
    "CentralAir": {"N": 0, "Y": 1},
    "Street": {"Grvl": 0, "Pave": 1},
})
# Not known at listing time, redundant with other fields, or near-constant.
DROP_COLS = [
    "Id", "SalePrice", "SaleType", "SaleCondition", "MoSold", "YrSold",
    "Utilities", "GarageYrBlt", "YearBuilt", "YearRemodAdd",
]
SALE_YEAR = 2010  # last sale year in the data; the app values homes "as of" this year
# Exterior2nd spells three materials differently from Exterior1st (found during the data-quality check).
EXTERIOR_FIX = {"Brk Cmn": "BrkComm", "CmentBd": "CemntBd", "Wd Shng": "WdShing"}
OUTLIER_RULE = "GrLivArea > 4000 and SalePrice < 300000"  # documented by the dataset author


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the two documented partial-sale outliers (huge houses sold for very low prices)."""
    return df[~((df["GrLivArea"] > 4000) & (df["SalePrice"] < 300_000))].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Preprocessing
# --------------------------------------------------------------------------- #
class AmesPreprocessor:
    """Cleaning + feature engineering + encoding. Everything data-dependent is learned in fit()."""

    def __init__(self, min_level_count: int = 3, skew_threshold: float = 0.75,
                 drop_features: tuple = (), keep_columns: tuple = ()):
        # drop_features / keep_columns exist so experiments can switch a feature off or on (see experiments.py)
        self.min_level_count = min_level_count
        self.skew_threshold = skew_threshold
        self.drop_features = tuple(drop_features)
        self.keep_columns = tuple(keep_columns)

    # -- stage 1: deterministic cleaning ---------------------------------- #
    def _stage1(self, df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        for c in NONE_CATS:
            d[c] = d[c].fillna("None")
        for c in ZERO_NUMS:
            d[c] = d[c].fillna(0)
        d["MSSubClass"] = d["MSSubClass"].astype(str)
        d["Exterior2nd"] = d["Exterior2nd"].replace(EXTERIOR_FIX)
        return d

    # -- stage 2: engineering + ordinal encoding --------------------------- #
    def _stage2(self, d: pd.DataFrame) -> pd.DataFrame:
        d = d.copy()
        d["LotFrontage"] = d["LotFrontage"].fillna(d["Neighborhood"].map(self.lot_frontage_by_nbhd_))
        d["LotFrontage"] = d["LotFrontage"].fillna(self.global_lot_frontage_)
        d["TotalSF"] = d["TotalBsmtSF"] + d["1stFlrSF"] + d["2ndFlrSF"]
        d["TotalBath"] = d["FullBath"] + 0.5 * d["HalfBath"] + d["BsmtFullBath"] + 0.5 * d["BsmtHalfBath"]
        d["TotalPorch"] = (d["OpenPorchSF"] + d["EnclosedPorch"] + d["3SsnPorch"]
                           + d["ScreenPorch"] + d["WoodDeckSF"])
        d["HouseAge"] = (SALE_YEAR - d["YearBuilt"]).clip(lower=0)
        d["RemodAge"] = (SALE_YEAR - d["YearRemodAdd"]).clip(lower=0)
        d["Remodeled"] = (d["YearRemodAdd"] != d["YearBuilt"]).astype(float)
        d["HasPool"] = (d["PoolArea"] > 0).astype(float)
        d["Has2ndFloor"] = (d["2ndFlrSF"] > 0).astype(float)
        d["HasGarage"] = (d["GarageArea"] > 0).astype(float)
        d["HasBasement"] = (d["TotalBsmtSF"] > 0).astype(float)
        d["HasFireplace"] = (d["Fireplaces"] > 0).astype(float)
        for col, mapping in ORDINALS.items():
            d[col] = d[col].map(mapping)
        drop = [c for c in DROP_COLS if c not in self.keep_columns] + list(self.drop_features)
        return d.drop(columns=[c for c in drop if c in d.columns])

    def _fill_modes(self, d: pd.DataFrame) -> pd.DataFrame:
        d = d.copy()
        for c, m in self.modes_.items():
            d[c] = d[c].fillna(m)
        return d

    # -- fit / transform ---------------------------------------------------- #
    def fit(self, df: pd.DataFrame) -> "AmesPreprocessor":
        self.raw_columns_ = [c for c in df.columns if c not in ("Id", "SalePrice")]
        d = self._stage1(df)
        obj_cols = [c for c in d.columns if d[c].dtype == object or str(d[c].dtype).startswith("str")]
        self.modes_ = {c: d[c].mode().iloc[0] for c in obj_cols}
        d = self._fill_modes(d)
        self.lot_frontage_by_nbhd_ = d.groupby("Neighborhood")["LotFrontage"].median().to_dict()
        self.global_lot_frontage_ = float(d["LotFrontage"].median())
        d = self._stage2(d)

        self.cat_cols_ = [c for c in d.columns if d[c].dtype == object or str(d[c].dtype).startswith("str")]
        self.num_cols_ = [c for c in d.columns if c not in self.cat_cols_]
        self.levels_ = {
            c: [lv for lv, n in d[c].value_counts().items() if n >= self.min_level_count]
            for c in self.cat_cols_
        }
        self.medians_ = d[self.num_cols_].median().to_dict()
        self.log_cols_ = [
            c for c in self.num_cols_
            if d[c].nunique() > 10 and d[c].min() >= 0 and abs(skew(d[c].fillna(self.medians_[c]))) > self.skew_threshold
        ]
        self.feature_names_ = self.num_cols_ + [f"{c}={lv}" for c in self.cat_cols_ for lv in self.levels_[c]]
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        d = self._fill_modes(self._stage1(df))
        d = self._stage2(d)
        out = d[self.num_cols_].astype(float).fillna(pd.Series(self.medians_))
        out[self.log_cols_] = np.log1p(out[self.log_cols_])
        dummies = {
            f"{c}={lv}": (d[c] == lv).astype(float)
            for c in self.cat_cols_ for lv in self.levels_[c]
        }
        out = pd.concat([out, pd.DataFrame(dummies, index=out.index)], axis=1)
        return out[self.feature_names_]


def feature_group(name: str) -> str:
    """One-hot columns 'Neighborhood=NAmes' roll up into their original variable."""
    return name.split("=")[0]


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
# Chosen by cross-validation in experiments.py (two-pass one-at-a-time search, training split only).
GBM_PARAMS = dict(
    n_estimators=600, learning_rate=0.02, num_leaves=16, min_child_samples=5,
    subsample=0.7, subsample_freq=1, colsample_bytree=0.4, reg_lambda=0.0,
    random_state=42, verbose=-1, n_jobs=1,
)


def make_lasso() -> LassoCV:
    return LassoCV(alphas=np.logspace(-4, -1.5, 30), cv=5, max_iter=50_000, random_state=42)


class PriceModel:
    """Average of a Lasso and a LightGBM model, both trained on log(1 + SalePrice)."""

    def __init__(self, w_linear: float = 0.5):
        self.w_linear = w_linear

    def fit(self, X: pd.DataFrame, y_log: np.ndarray) -> "PriceModel":
        self.pre = AmesPreprocessor().fit(X)
        Xp = self.pre.transform(X)
        self.scaler = StandardScaler().fit(Xp)
        self.lasso = make_lasso().fit(self.scaler.transform(Xp), y_log)
        self.gbm = lgb.LGBMRegressor(**GBM_PARAMS).fit(Xp.values, y_log)
        return self

    def predict_components(self, X: pd.DataFrame) -> dict:
        Xp = self.pre.transform(X)
        return {
            "lasso": self.lasso.predict(self.scaler.transform(Xp)),
            "lightgbm": self.gbm.predict(Xp.values),
        }

    def predict_log(self, X: pd.DataFrame) -> np.ndarray:
        c = self.predict_components(X)
        return self.w_linear * c["lasso"] + (1 - self.w_linear) * c["lightgbm"]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.expm1(self.predict_log(X))

    def contributions(self, X: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
        """Additive contribution of each original variable to the log-price, relative to an average home.

        Lasso part: coefficient x standardised value (exact). LightGBM part: TreeSHAP values
        (LightGBM's built-in pred_contrib). Both are blended with the same weights as the prediction,
        so bias + sum(contributions) equals predict_log(X).
        """
        Xp = self.pre.transform(X)
        lin = self.scaler.transform(Xp) * self.lasso.coef_
        gbm = self.gbm.predict(Xp.values, pred_contrib=True)
        w = self.w_linear
        contrib = w * lin + (1 - w) * gbm[:, :-1]
        bias = w * self.lasso.intercept_ + (1 - w) * gbm[:, -1]
        cdf = pd.DataFrame(contrib, columns=self.pre.feature_names_, index=X.index)
        grouped = cdf.T.groupby(feature_group).sum().T
        return grouped, bias


# --------------------------------------------------------------------------- #
# App-side helpers: defaults, row building, estimate
# --------------------------------------------------------------------------- #
def compute_defaults(df: pd.DataFrame) -> dict:
    """Typical values per neighbourhood (median for numbers, most common for categories)."""
    d = df.drop(columns=["Id", "SalePrice"], errors="ignore").copy()
    for c in NONE_CATS:
        d[c] = d[c].fillna("None")
    for c in ZERO_NUMS:
        d[c] = d[c].fillna(0)
    d["MSSubClass"] = d["MSSubClass"].astype(str)

    def summarise(g: pd.DataFrame) -> dict:
        out = {}
        for c in g.columns:
            s = g[c].dropna()
            if s.empty:
                continue
            is_num = pd.api.types.is_numeric_dtype(s)
            v = s.median() if is_num else s.mode().iloc[0]
            out[c] = float(v) if is_num else str(v)
        return out

    per_car = (df["GarageArea"] / df["GarageCars"].replace(0, np.nan)).median()
    return {
        "raw_columns": [c for c in df.columns if c not in ("Id", "SalePrice")],
        "overall": summarise(d),
        "by_neighborhood": {n: summarise(g) for n, g in d.groupby("Neighborhood")},
        "neighborhood_counts": d["Neighborhood"].value_counts().to_dict(),
        "garage_area_per_car": float(per_car),
    }


# Variables the user provides directly in the app (everything else is a neighbourhood-typical assumption).
USER_GROUPS = {
    "Neighborhood", "GrLivArea", "TotalSF", "1stFlrSF", "2ndFlrSF", "Has2ndFloor", "HouseStyle", "MSSubClass",
    "LotArea", "OverallQual", "HouseAge", "RemodAge", "Remodeled", "GarageCars", "GarageArea", "HasGarage",
    "TotalBsmtSF", "HasBasement", "TotalBath", "FullBath", "HalfBath", "KitchenQual", "OverallCond",
}
FRIENDLY = {
    "OverallQual": "Overall quality", "OverallCond": "Overall condition", "GrLivArea": "Living area", "TotalSF": "Total floor area",
    "Neighborhood": "Neighbourhood", "HouseAge": "House age", "RemodAge": "Years since remodel",
    "Remodeled": "Remodelled", "GarageCars": "Garage capacity", "GarageArea": "Garage size",
    "HasGarage": "Has garage", "TotalBsmtSF": "Basement area", "HasBasement": "Has basement",
    "TotalBath": "Bathrooms", "KitchenQual": "Kitchen quality", "LotArea": "Lot size",
    "1stFlrSF": "First-floor area", "2ndFlrSF": "Second-floor area", "Has2ndFloor": "Has second floor",
    "ExterQual": "Exterior quality", "BsmtQual": "Basement quality", "FireplaceQu": "Fireplace quality",
    "HasFireplace": "Has fireplace", "Fireplaces": "Fireplaces", "BsmtFinSF1": "Finished basement area",
    "CentralAir": "Central air", "MSZoning": "Zoning", "MSSubClass": "Dwelling type",
    "HouseStyle": "House style", "TotalPorch": "Porch/deck area", "GarageFinish": "Garage finish",
    "HeatingQC": "Heating quality", "BsmtExposure": "Basement exposure", "LotFrontage": "Lot frontage",
    "Functional": "Home functionality", "FullBath": "Full bathrooms", "HalfBath": "Half bathrooms",
}


def build_row(inputs: dict, defaults: dict) -> pd.DataFrame:
    """Build a full raw row from the app inputs.

    Required keys: Neighborhood, GrLivArea, Stories (1 or 2), LotArea, OverallQual, YearBuilt,
    YearRemodAdd, GarageCars, TotalBsmtSF, FullBath, HalfBath, KitchenQual. Optional: OverallCond.
    Everything else comes from the neighbourhood's typical home.
    """
    nb = inputs["Neighborhood"]
    row = dict(defaults["overall"])
    row.update(defaults["by_neighborhood"].get(nb, {}))
    row["Neighborhood"] = nb

    gliv = float(inputs["GrLivArea"])
    two = int(inputs["Stories"]) == 2
    row["GrLivArea"] = gliv
    row["1stFlrSF"] = round(gliv * 0.55) if two else gliv
    row["2ndFlrSF"] = gliv - row["1stFlrSF"] if two else 0.0
    row["HouseStyle"] = "2Story" if two else "1Story"
    row["MSSubClass"] = "60" if two else "20"

    for k in ("LotArea", "OverallQual", "YearBuilt", "YearRemodAdd", "FullBath", "HalfBath"):
        row[k] = float(inputs[k])
    row["KitchenQual"] = inputs["KitchenQual"]
    if inputs.get("OverallCond") is not None:  # optional; otherwise the neighbourhood's typical condition
        row["OverallCond"] = float(inputs["OverallCond"])
    row["YearRemodAdd"] = max(row["YearRemodAdd"], row["YearBuilt"])

    cars = int(inputs["GarageCars"])
    row["GarageCars"] = float(cars)
    row["GarageArea"] = round(cars * defaults["garage_area_per_car"])
    if cars == 0:
        for c in ("GarageType", "GarageFinish", "GarageQual", "GarageCond"):
            row[c] = "None"

    bsmt = float(inputs["TotalBsmtSF"])
    old_fin = row.get("BsmtFinSF1", 0.0) + row.get("BsmtFinSF2", 0.0) + row.get("BsmtUnfSF", 0.0)
    if bsmt <= 0:
        row.update(TotalBsmtSF=0.0, BsmtFinSF1=0.0, BsmtFinSF2=0.0, BsmtUnfSF=0.0,
                   BsmtFullBath=0.0, BsmtHalfBath=0.0)
        for c in ("BsmtQual", "BsmtCond", "BsmtExposure", "BsmtFinType1", "BsmtFinType2"):
            row[c] = "None"
    else:
        scale = bsmt / old_fin if old_fin > 0 else 0.0
        row["TotalBsmtSF"] = bsmt
        row["BsmtFinSF1"] = row.get("BsmtFinSF1", 0.0) * scale
        row["BsmtFinSF2"] = row.get("BsmtFinSF2", 0.0) * scale
        row["BsmtUnfSF"] = bsmt - row["BsmtFinSF1"] - row["BsmtFinSF2"]

    row["YrSold"] = SALE_YEAR
    # Year built must exist even though it is dropped after computing age.
    cols = [c for c in defaults["raw_columns"]]
    return pd.DataFrame([{c: row.get(c, np.nan) for c in cols}])


def estimate(model: PriceModel, defaults: dict, inputs: dict, rmsle: float, top_n: int = 5) -> dict:
    """Price estimate, a typical-error range (+/- one holdout RMSLE) and the top drivers."""
    X = build_row(inputs, defaults)
    price = float(model.predict(X)[0])
    grouped, _ = model.contributions(X)
    c = grouped.iloc[0]
    top = c.reindex(c.abs().sort_values(ascending=False).index).head(top_n)
    drivers = [
        {
            "feature": g,
            "label": FRIENDLY.get(g, g),
            "effect_pct": float(np.expm1(v) * 100),
            "from_user": g in USER_GROUPS,
        }
        for g, v in top.items()
    ]
    return {
        "price": price,
        "low": price * float(np.exp(-rmsle)),
        "high": price * float(np.exp(rmsle)),
        "drivers": drivers,
    }


# --------------------------------------------------------------------------- #
# Input validation (the "Input validation" box in the architecture)
# --------------------------------------------------------------------------- #
KITCHEN_CODES = {"Ex": "Excellent", "Gd": "Good", "TA": "Typical / average", "Fa": "Fair", "Po": "Poor"}
# field: (label, minimum, maximum, whole number?, required?)  min/max are hard limits: outside them the input is rejected.
FIELD_RULES = {
    "GrLivArea": ("Living area (sq ft)", 200, 10_000, False, True),
    "LotArea": ("Lot size (sq ft)", 500, 200_000, False, True),
    "TotalBsmtSF": ("Basement area (sq ft)", 0, 10_000, False, True),
    "OverallQual": ("Overall quality", 1, 10, True, True),
    "OverallCond": ("Overall condition", 1, 10, True, False),
    "YearBuilt": ("Year built", 1800, SALE_YEAR, True, True),
    "YearRemodAdd": ("Year remodelled", 1800, SALE_YEAR, True, True),
    "GarageCars": ("Garage capacity", 0, 6, True, True),
    "FullBath": ("Full bathrooms", 0, 6, True, True),
    "HalfBath": ("Half bathrooms", 0, 4, True, True),
    "Stories": ("Stories", 1, 2, True, True),
}


def _to_number(v):
    """Return (number, error). Accepts numbers and numeric text such as '1,500'."""
    if isinstance(v, bool):
        return None, "must be a number"
    if isinstance(v, str):
        v = v.strip().replace(",", "")
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None, "must be a number"
    if not np.isfinite(x):
        return None, "must be a finite number"
    return x, None


def validate_inputs(inputs: dict, defaults: dict) -> dict:
    """Check and clean the user inputs.

    Returns {"clean": dict, "errors": [str], "warnings": [str]}.
    Errors mean the estimate must not be produced. Warnings mean it is produced but should be read with care.
    """
    clean, errors, warnings = {}, [], []
    rng = defaults.get("ranges", {})

    for key, (label, lo, hi, whole, required) in FIELD_RULES.items():
        v = inputs.get(key)
        if v is None or (isinstance(v, str) and not v.strip()):
            if required:
                errors.append(f"{label} is required.")
            continue
        x, err = _to_number(v)
        if err:
            errors.append(f"{label} {err} (got {v!r}).")
            continue
        if whole and x != round(x):
            errors.append(f"{label} must be a whole number (got {v!r}).")
            continue
        if not lo <= x <= hi:
            errors.append(f"{label} must be between {lo:,} and {hi:,} (got {x:,.0f}).")
            continue
        clean[key] = int(x) if whole else x

    kq = inputs.get("KitchenQual")
    if kq is None or (isinstance(kq, str) and not kq.strip()):
        errors.append("Kitchen quality is required.")
    elif str(kq).strip() not in KITCHEN_CODES:
        errors.append(f"Kitchen quality must be one of {', '.join(KITCHEN_CODES)} (got {kq!r}).")
    else:
        clean["KitchenQual"] = str(kq).strip()

    nb = inputs.get("Neighborhood")
    if nb is None or (isinstance(nb, str) and not nb.strip()):
        errors.append("Neighbourhood is required.")
    elif not isinstance(nb, str) or len(nb.strip()) > 60:
        # JSON clients can send numbers, lists or huge strings; only the Streamlit dropdown guaranteed clean text
        errors.append(f"Neighbourhood must be text of at most 60 characters (got {str(nb)[:30]!r}).")
    else:
        known = {n.lower(): n for n in defaults["by_neighborhood"]}
        match = known.get(str(nb).strip().lower())
        if match:
            clean["Neighborhood"] = match
        else:
            clean["Neighborhood"] = str(nb).strip()
            warnings.append(f"Neighbourhood {nb!r} is not one the model learned from. City-wide typical values "
                            "were used and the estimate is less reliable.")

    if errors:
        return {"clean": clean, "errors": errors, "warnings": warnings}

    if clean["YearRemodAdd"] < clean["YearBuilt"]:
        clean["YearRemodAdd"] = clean["YearBuilt"]
        warnings.append("Remodel year was before the year built, so the year built was used instead.")
    if rng:
        lo, hi = rng["GrLivArea"]
        if not lo <= clean["GrLivArea"] <= hi:
            warnings.append(f"Living area is outside the {lo:,} to {hi:,} sq ft the model learned from; "
                            "the estimate is an extrapolation.")
        if clean["LotArea"] > rng["LotArea"][1]:
            warnings.append("Lot size is unusually large compared with the training data (top 1%).")
        if clean["TotalBsmtSF"] > rng["TotalBsmtSF"][1]:
            warnings.append("Basement area is larger than any home in the training data.")
        if clean["YearBuilt"] < rng["YearBuilt"][0]:
            warnings.append("Year built is earlier than any home in the training data.")
    clean["Stories"] = int(clean["Stories"])
    return {"clean": clean, "errors": errors, "warnings": warnings}


def safe_estimate(model: PriceModel, defaults: dict, inputs: dict, rmsle: float) -> dict:
    """Validate, then estimate. Never raises: returns {"ok", "errors", "warnings", "result"}."""
    v = validate_inputs(inputs, defaults)
    if v["errors"]:
        return {"ok": False, "errors": v["errors"], "warnings": v["warnings"], "result": None}
    try:
        res = estimate(model, defaults, v["clean"], rmsle)
    except Exception as exc:  # pragma: no cover - last-resort guard so the app never shows a stack trace
        return {"ok": False, "errors": [f"The estimate could not be computed ({type(exc).__name__})."],
                "warnings": v["warnings"], "result": None}
    return {"ok": True, "errors": [], "warnings": v["warnings"], "result": res}
