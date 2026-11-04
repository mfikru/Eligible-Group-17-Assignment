"""Streamlit app: estimate a home's sale price and show what drives the estimate.

Run:  streamlit run app.py
"""
import json
import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import artifacts
import housing as h
import prediction_log as plog

ROOT = Path(__file__).parent

NEIGHBORHOODS = {
    "Blmngtn": "Bloomington Heights", "Blueste": "Bluestem", "BrDale": "Briardale", "BrkSide": "Brookside",
    "ClearCr": "Clear Creek", "CollgCr": "College Creek", "Crawfor": "Crawford", "Edwards": "Edwards",
    "Gilbert": "Gilbert", "IDOTRR": "Iowa DOT and Rail Road", "MeadowV": "Meadow Village",
    "Mitchel": "Mitchell", "NAmes": "North Ames", "NoRidge": "Northridge", "NPkVill": "Northpark Villa",
    "NridgHt": "Northridge Heights", "NWAmes": "Northwest Ames", "OldTown": "Old Town",
    "SWISU": "South & West of Iowa State University", "Sawyer": "Sawyer", "SawyerW": "Sawyer West",
    "Somerst": "Somerset", "StoneBr": "Stone Brook", "Timber": "Timberland", "Veenker": "Veenker",
}
KITCHEN = h.KITCHEN_CODES
QUALITY_HELP = (
    "1 = very poor, 5 = average, 10 = very excellent. Judge the materials and finish of the house."
)

st.set_page_config(page_title="Home Price Estimator (Ames, Iowa)", page_icon="🏠", layout="wide")


@st.cache_resource
def load_artifacts():
    return artifacts.load_artifacts()


model, defaults, info = load_artifacts()
rng = defaults["ranges"]
range_err = artifacts.range_rmsle(info)

if range_err is None:
    st.warning(
        "Holdout RMSLE is not available. "
        "Please provide the actual model evaluation result."
    )
app_base = artifacts.load_app_baseline()
ach = info["targets_vs_achieved"]

st.title("🏠 Home Price Estimator")
st.caption(
    "Estimates the market value of a home in **Ames, Iowa** from its main features, and shows what pushes the "
    "price up or down. Trained on 1,458 home sales from 2006 to 2010. **An estimate only, not an appraisal, and "
    "not for lending decisions.**"
)

left, right = st.columns([1, 1.15], gap="large")

with left:
    st.subheader("Describe the home")
    nb_codes = sorted(defaults["by_neighborhood"], key=lambda c: NEIGHBORHOODS.get(c, c))
    nb = st.selectbox("Neighbourhood", nb_codes, index=nb_codes.index("NAmes"),
                      format_func=lambda c: NEIGHBORHOODS.get(c, c))
    c1, c2 = st.columns(2)
    gliv = c1.number_input("Living area (sq ft, above ground)", 0, 20_000, 1500, step=50)
    stories = c2.radio("Stories", [1, 2], horizontal=True)
    c3, c4 = st.columns(2)
    lot = c3.number_input("Lot size (sq ft)", 0, 500_000, 9000, step=500)
    bsmt = c4.number_input("Basement area (sq ft, 0 if none)", 0, 20_000, 900, step=50)
    qual = st.slider("Overall quality (1 to 10)", 1, 10, 6, help=QUALITY_HELP)
    cond = st.slider("Overall condition (1 to 10)", 1, 10, 5,
                     help="1 = very poor, 5 = average, 10 = very excellent. Judge the current state of repair.")
    c5, c6 = st.columns(2)
    built = c5.number_input("Year built", 1600, 2100, 1975)
    remod = c6.number_input("Year remodelled (same as built if never)", 1600, 2100, max(1990, built))
    c7, c8, c9 = st.columns(3)
    cars = c7.selectbox("Garage capacity (cars)", [0, 1, 2, 3, 4], index=2)
    full = c8.selectbox("Full bathrooms", [0, 1, 2, 3, 4], index=2)
    half = c9.selectbox("Half bathrooms", [0, 1, 2], index=0)
    kitchen = st.select_slider("Kitchen quality", options=list(KITCHEN), value="TA",
                               format_func=lambda k: KITCHEN[k])

inputs = {
    "Neighborhood": nb, "GrLivArea": gliv, "Stories": stories, "LotArea": lot, "OverallQual": qual,
    "OverallCond": cond, "YearBuilt": built, "YearRemodAdd": remod, "GarageCars": cars,
    "TotalBsmtSF": bsmt, "FullBath": full, "HalfBath": half, "KitchenQual": kitchen,
}
t0 = time.perf_counter()
out = h.safe_estimate(model, defaults, inputs, range_err)
latency_ms = (time.perf_counter() - t0) * 1000

# Log each distinct set of inputs once per session (Streamlit reruns on every widget change). No personal data is stored.
signature = json.dumps(inputs, sort_keys=True, default=str)
if st.session_state.get("_logged_signature") != signature:
    st.session_state["_logged_signature"] = signature
    st.session_state["_request_id"] = plog.log_prediction(
        inputs, out, source="streamlit", latency_ms=latency_ms)

with right:
    st.subheader("Estimate")
    if not out["ok"]:
        st.error("The estimate cannot be produced yet. Please fix the following:")
        for e in out["errors"]:
            st.error(e)
        st.stop()
    result = out["result"]
    st.metric("Estimated sale price", f"${result['price']:,.0f}")
    st.write(
        f"Typical range: **${result['low']:,.0f} to ${result['high']:,.0f}** "
        f"(about ±{range_err * 100:.0f}%, the typical error of this form on homes it had not seen)."
    )
    for w in out["warnings"]:
        st.warning(w)

    st.subheader("What drives this estimate")
    drv = pd.DataFrame(result["drivers"])
    drv["source"] = drv["from_user"].map({True: "from your inputs", False: "typical for the neighbourhood"})
    chart = (
        alt.Chart(drv)
        .mark_bar()
        .encode(
            x=alt.X("effect_pct:Q", title="Effect on price compared with an average Ames home (%)"),
            y=alt.Y("label:N", sort=None, title=None),
            color=alt.condition(alt.datum.effect_pct > 0, alt.value("#2f855a"), alt.value("#c53030")),
            tooltip=["label", alt.Tooltip("effect_pct:Q", format="+.1f"), "source"],
        )
        .properties(height=230)
    )
    st.altair_chart(chart, width="stretch")
    for d in result["drivers"]:
        st.write(f"- **{d['label']}**: {d['effect_pct']:+.1f}% "
                 f"({'from your inputs' if d['from_user'] else 'assumed, typical for the neighbourhood'})")
    st.caption("Change any input on the left to see how the estimate and its drivers move.")

    if app_base:
        app_line = (f"RMSLE **{app_base['rmsle']:.3f}**, mean absolute error **${app_base['mae']:,.0f}**, and "
                    f"**{app_base['within_15pct'] * 100:.0f}%** within 15% of the actual price.")
        range_line = (f"about {app_base['range_coverage_with_own_range'] * 100:.0f}% of the held-back homes fell inside it, "
                      "so roughly one in four will fall outside.")
    else:
        app_line = "lower than the line above (not yet measured)."
        range_line = "about three in four held-back homes fell inside the range for all-feature estimates."
    with st.expander("How this works and its limits"):
        st.markdown(
            f"""
- **Model:** average of a Lasso regression and a LightGBM model trained on log price, using {info['n_model_features']} engineered features.
- **Accuracy on 292 homes held back from training, using all 79 recorded features:** typical error (RMSLE) **{ach['rmsle']['holdout']:.3f}**,
  mean absolute error **${ach['mae_usd']['holdout']:,.0f}**, R² **{ach['r2']['holdout']:.2f}**,
  and **{ach['within_15pct']['holdout'] * 100:.0f}%** of estimates within 15% of the actual price.
- **Accuracy through this form (13 fields; the rest are typical values):** {app_line}
- **The range is not a guarantee:** {range_line}
- **Fields you do not enter** (roof, heating, fireplaces, etc.) are set to what is typical in the chosen neighbourhood.
- **Valuation date:** homes are valued as of 2010, the last year in the data. Prices have changed since then.
- **Where it is weaker:** cheaper, older homes in neighbourhoods such as Old Town and Iowa DOT and Rail Road, where the model tends to over-estimate.
- **Not valid** for other cities, and it cannot see condition details, renovations or views that are not in the fields above.
"""
        )

    request_id = st.session_state.get("_request_id")
    if plog.logging_enabled() and request_id:
        with st.expander("Help check the model: do you know the real sale price?"):
            actual = st.number_input("Actual sale price (USD)", 0, 5_000_000, 0, step=1000, key="actual_price")
            if st.button("Record sale price"):
                if actual > 0 and plog.log_outcome(request_id, actual):
                    st.success("Recorded. It is used to measure how accurate the estimates are.")
                else:
                    st.error("Please enter a sale price above zero.")

if plog.logging_enabled():
    st.caption("Privacy: the values you enter (and the estimate) are logged without any personal details, to monitor "
               "accuracy. Nothing identifies you. Set the environment variable PRICE_LOG=0 to switch logging off.")
