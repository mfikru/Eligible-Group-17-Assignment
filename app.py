"""Streamlit demo: estimate an Ames house sale price from key property features.

Run:  streamlit run app.py
"""
import streamlit as st

from src import config
from src.predict import ModelNotFoundError, load_bundle, predict_price

st.set_page_config(page_title="House Price Estimator - Group 17", page_icon="🏠")
st.title("🏠 House Price Estimator")
st.caption("Group 17 · FUSE AI-201 · Prototype trained on the public Kaggle Ames Housing data "
           "(real historical sales from Ames, Iowa, 2006-2010). Not a professional valuation.")


@st.cache_resource
def get_bundle():
    return load_bundle()


try:
    model, metadata = get_bundle()
except ModelNotFoundError as e:
    st.error(str(e))
    st.stop()

with st.form("house_form"):
    payload = {}
    cols = st.columns(2)
    for i, (name, (label, kind, lo, hi, default, help_)) in enumerate(config.FORM_FIELDS.items()):
        with cols[i % 2]:
            if kind == "cat":
                levels = metadata["categorical_levels"][name]
                payload[name] = st.selectbox(label, levels,
                                             index=levels.index(default) if default in levels else 0,
                                             help=help_ or None)
            else:
                # No min/max on the widget on purpose: our validator reports out-of-range values
                # with a clear message instead of the widget silently clamping them.
                payload[name] = st.number_input(label, value=default, step=1, help=help_ or None)
    submitted = st.form_submit_button("Estimate price")

if submitted:
    result = predict_price(payload, model, metadata)
    if not result["ok"]:
        for err in result["errors"]:
            st.error(err)
    else:
        st.success(f"Estimated sale price: **${result['prediction']:,.0f}**")
        st.write(f"Rough range: ${result['low']:,.0f} - ${result['high']:,.0f} "
                 "(± one validation RMSLE; indicative only).")
        for w in result["warnings"]:
            st.warning(w)
        with st.expander("What was sent to the model"):
            st.json(payload)
            st.caption(f"The other {len(metadata['feature_columns']) - len(payload)} features "
                       "use training-set medians / most common values.")

with st.sidebar:
    st.subheader("Model info")
    m = metadata["validation_metrics"]
    st.write(f"Model: **{metadata['best_model']}**")
    st.write(f"Validation RMSLE: {m['RMSLE']:.4f}")
    st.write(f"Validation MAE: ${m['MAE']:,.0f}")
    st.write(f"Validation R²: {m['R2']:.3f}")
    st.caption("Metrics are from a held-out 20% validation split of Ames data, "
               "not from live use.")
