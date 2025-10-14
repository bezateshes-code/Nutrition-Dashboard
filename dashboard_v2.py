import streamlit as st
import pandas as pd

st.set_page_config(page_title="Nutrition Dashboard", layout="wide")

st.title("📊 Nutrition Dashboard")

# Example dummy data
df = pd.DataFrame({
    "year": [2020, 2021, 2022, 2023],
    "TFP_rate_per10k": [0, 0, 0, 0],
    "conflict_events_zone": [0, 0, 0, 0],
    "wrsi_value_leap": [6, 25, 54, 97],
    "ipc_value": [None, None, None, None]
})

# Tabs
tab1, tab2, tab3 = st.tabs(["Overlay", "Retrospective", "Data Quality"])

with tab1:
    st.subheader("Overlay Table")
    st.dataframe(df)

with tab2:
    st.subheader("Retrospective Analysis")
    st.write("Correlation, lagged correlation, and event-study tables will go here.")

with tab3:
    st.subheader("Data Quality")
    st.write("Coverage matrix and heatmaps will go here.")

