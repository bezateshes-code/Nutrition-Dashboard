
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title='Ethiopia GAM Dashboard', layout='wide')

@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path, parse_dates=['date'])
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            return None

TS = load_csv('dhis_woreda_month_timeseries.csv')
VAR = load_csv('dhis_variability_summary.csv')
RET = load_csv('dhis_recent12m_retrospective.csv')
WF = load_csv('forecasts_woreda_2025_11_12.csv')
RF = load_csv('forecasts_region_2025_11_12.csv')
NF = load_csv('forecasts_national_2025_11_12.csv')

st.title('Ethiopia GAM Forecasting Dashboard')
st.caption('Powered by Julius (https://julius.ai). Data shown: DHIS-derived summaries and forecasts.')

st.sidebar.header('Filters')
region_sel = None
woreda_sel = None

if TS is not None and 'region' in TS.columns:
    regions = sorted([r for r in TS['region'].dropna().unique()])
    region_sel = st.sidebar.selectbox('Region', ['All'] + regions)
    if region_sel != 'All' and 'woreda' in TS.columns:
        woredas = sorted([w for w in TS.loc[TS['region'] == region_sel, 'woreda'].dropna().unique()])
        woreda_sel = st.sidebar.selectbox('Woreda', ['All'] + woredas)

st.header('Time Series')
if TS is not None and 'date' in TS.columns and 'acute_cases' in TS.columns:
    df = TS.copy()
    if region_sel and region_sel != 'All':
        df = df[df['region'] == region_sel]
    if woreda_sel and woreda_sel != 'All':
        df = df[df['woreda'] == woreda_sel]
    df = df.dropna(subset=['date'])
    chart = alt.Chart(df).mark_line().encode(
        x='date:T', y='acute_cases:Q', color=alt.Color('woreda:N', legend=None if woreda_sel and woreda_sel != 'All' else alt.Legend())
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info('Time series not available.')

st.header('Recent 12m Retrospective')
if RET is not None and 'woreda' in RET.columns:
    st.dataframe(RET.head(50))
else:
    st.info('Retrospective not available.')

st.header('Forecasts Nov-Dec 2025')
cols = st.columns(3)
with cols[0]:
    st.subheader('Woreda level')
    if WF is not None:
        st.dataframe(WF.head(100))
    else:
        st.info('No woreda-level forecast file.')
with cols[1]:
    st.subheader('Region level')
    if RF is not None:
        st.dataframe(RF.head(100))
    else:
        st.info('No region-level forecast file.')
with cols[2]:
    st.subheader('National total')
    if NF is not None:
        st.dataframe(NF)
    else:
        st.info('No national forecast file.')

st.header('Variability Snapshot')
if VAR is not None:
    st.dataframe(VAR.head(20))
else:
    st.info('Variability file not available.')

st.header('Performance Metrics')
st.markdown('- Fit: Average difference between predicted and actual GAM rates (requires backtests).')
st.markdown('- Accuracy: Match between predicted IPC classification and observed (if available).')
st.markdown('- Stability: Performance across woredas and time (rolling).')
st.markdown('- Benchmarking: Compare to naive/seasonal mean baselines.')

st.caption('Add LEAP, climate, demographics, and conflict by dropping CSVs here and extending the model join in code.')
