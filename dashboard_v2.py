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
    st.info("This section will show lagged correlations, event-study tables, and retrospective diagnostics.")
    
    # Example placeholder chart
    import numpy as np
    import pandas as pd
    import altair as alt
    
    dummy = pd.DataFrame({
        "Month": pd.date_range("2020-01-01", periods=12, freq="M"),
        "TFP_rate": np.random.rand(12) * 10
    })
    chart = alt.Chart(dummy).mark_line().encode(
        x="Month",
        y="TFP_rate"
    )
    st.altair_chart(chart, use_container_width=True)


with tab3:
    st.subheader("Data Quality")
    st.info("This section will display coverage matrices and heatmaps for DHIS, conflict, WRSI, and IPC data.")
    
    # Example placeholder coverage table
    coverage = pd.DataFrame({
        "Indicator": ["TFP", "Conflict", "WRSI", "IPC"],
        "Coverage %": [100, 95, 90, 0]
    })
    st.table(coverage)

