import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Nutrition Dashboard", layout="wide")
st.title("📊 Nutrition Dashboard")

# -------------------------------------------------------------------
# DATA LOADING — update master_file to your latest integrated CSV
# -------------------------------------------------------------------
BASE = Path("D:/dash_outputs/missingness")
master_file = BASE / "processed/master_integrated_dhis_conflict_ipc_wrsi.20251014T054322Z.csv"  # update to latest

# Guarded load with clear error
try:
    df = pd.read_csv(master_file, parse_dates=["ym_ts"])
except FileNotFoundError:
    st.error(f"File not found: {master_file}. Please update the path/filename to your latest integrated CSV.")
    st.stop()

# Normalize required keys if present
for col in ["ADM2_PCODE", "ADM2_PCODE_final2"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
# Canonical ADM2 column
ADM2_COL = "ADM2_PCODE" if "ADM2_PCODE" in df.columns else ("ADM2_PCODE_final2" if "ADM2_PCODE_final2" in df.columns else None)
if ADM2_COL is None:
    st.warning("ADM2 key not found (expected ADM2_PCODE or ADM2_PCODE_final2). Some retrospective outputs will be limited.")

# Ensure ym_ts is datetime
if "ym_ts" in df.columns and not np.issubdtype(df["ym_ts"].dtype, np.datetime64):
    df["ym_ts"] = pd.to_datetime(df["ym_ts"], errors="coerce")

# Build TFP_rate_per10k if needed
if {"SAM", "MAM"}.issubset(df.columns):
    df["TFP_total"] = df[["SAM", "MAM"]].sum(axis=1)
    if "population" in df.columns and (df["population"] > 0).any():
        df["TFP_rate_per10k"] = (df["TFP_total"] / df["population"]) * 10000
    elif "TFP_rate_per10k" not in df.columns:
        # Use total as proxy when population missing
        df["TFP_rate_per10k"] = df["TFP_total"]
elif "TFP_rate_per10k" not in df.columns:
    st.warning("TFP_rate_per10k not found and SAM/MAM unavailable. Retrospective targets may be limited.")

# -------------------------------------------------------------------
# HELPER FUNCTIONS — robust to sparse coverage and minimal columns
# -------------------------------------------------------------------
def overlay_table(data: pd.DataFrame, rows: int = 24, woreda: str | None = None) -> pd.DataFrame:
    """Tabular snapshot of key variables over time for a woreda (or pooled)."""
    if "ym_ts" in data.columns:
        out = data.copy().sort_values("ym_ts")
    else:
        out = data.copy()

    if woreda and ADM2_COL and ADM2_COL in out.columns:
        out = out[out[ADM2_COL] == woreda]

    cols = [c for c in ["ADM2_PCODE", "ym_ts", "TFP_rate_per10k", "conflict_events_zone", "wrsi_value_leap", "ipc_value"] if c in out.columns]
    if not cols:
        # Minimal fallback: show what exists
        cols = [c for c in ["year", "TFP_rate_per10k", "conflict_events_zone", "wrsi_value_leap", "ipc_value"] if c in out.columns]
    return out[cols].head(rows) if cols else out.head(rows)

def safe_corr(x: pd.Series, y: pd.Series) -> float | float:
    """Compute Pearson corr only if both series have >2 valid and non-constant values."""
    mask = x.notna() & y.notna()
    if mask.sum() > 2 and x[mask].nunique() > 1 and y[mask].nunique() > 1:
        return x[mask].corr(y[mask])
    return np.nan

def lagged_corr_table(data: pd.DataFrame,
                      features=("conflict_events_zone", "wrsi_value_leap"),
                      lags=range(0, 4)) -> pd.DataFrame:
    """Table of correlations between TFP and lagged features across all woredas pooled."""
    if "TFP_rate_per10k" not in data.columns:
        return pd.DataFrame({"Note": ["TFP_rate_per10k missing; cannot compute correlations"]})

    # If ADM2/time missing, return NaNs honestly
    if ADM2_COL is None or "ym_ts" not in data.columns:
        return pd.DataFrame({feat: [np.nan for _ in lags] for feat in features},
                            index=[f"Lag {l}" for l in lags])

    out = {}
    for feat in features:
        vals = []
        for lag in lags:
            shifted = data.groupby(ADM2_COL)[feat].shift(lag) if feat in data.columns else pd.Series(index=data.index, dtype="float64")
            vals.append(safe_corr(data["TFP_rate_per10k"], shifted))
        out[feat] = vals
    return pd.DataFrame(out, index=[f"Lag {l}" for l in lags])

def event_study_table(data: pd.DataFrame,
                      feature="conflict_events_zone",
                      target="TFP_rate_per10k",
                      shock_type="high",
                      threshold_value=None,
                      window=(-1, 2)) -> pd.DataFrame:
    """Average target trajectory around shocks (pooled across woredas)."""
    needed = {"ym_ts", target, feature}
    if ADM2_COL is None:
        # Still allow pooled event-study without ADM2, but quality is lower
        needed = {"ym_ts", target, feature}
    else:
        needed = {"ym_ts", target, feature, ADM2_COL}

    if not needed.issubset(set(data.columns)):
        return pd.DataFrame({"Months_relative": [], f"Avg_{target}": []})

    df2 = data.copy().sort_values([ADM2_COL, "ym_ts"]) if ADM2_COL else data.copy().sort_values("ym_ts")

    # Inclusive thresholds for sparse data
    if threshold_value is None:
        threshold_value = 0 if shock_type == "high" else df2[feature].median()

    if shock_type == "high":
        shocks = df2.loc[df2[feature] > threshold_value, [ADM2_COL, "ym_ts"]] if ADM2_COL else df2.loc[df2[feature] > threshold_value, ["ym_ts"]]
    else:
        shocks = df2.loc[df2[feature] < threshold_value, [ADM2_COL, "ym_ts"]] if ADM2_COL else df2.loc[df2[feature] < threshold_value, ["ym_ts"]]

    if shocks.empty:
        return pd.DataFrame({"Months_relative": [], f"Avg_{target}": []})

    before, after = window
    windows = []
    for _, row in shocks.iterrows():
        if ADM2_COL:
            woreda, t = row[ADM2_COL], row["ym_ts"]
            sub = df2[df2[ADM2_COL] == woreda].set_index("ym_ts")
        else:
            t = row["ym_ts"]
            sub = df2.set_index("ym_ts")
        rel_index = list(range(before, after + 1))
        vals = []
        for rel in rel_index:
            dt = t + pd.DateOffset(months=rel)
            vals.append(sub.at[dt, target] if dt in sub.index else np.nan)
        s = pd.Series(vals, index=rel_index)
        if s.notna().any():
            windows.append(s)

    if not windows:
        return pd.DataFrame({"Months_relative": [], f"Avg_{target}": []})

    avg = pd.concat(windows, axis=1).mean(axis=1)
    return avg.rename(f"Avg_{target}").reset_index().rename(columns={"index": "Months_relative"})

def coverage_tables(data: pd.DataFrame):
    """Return compact coverage summaries (overall and by year)."""
    vars_interest = [c for c in ["TFP_rate_per10k", "conflict_events_zone", "wrsi_value_leap", "ipc_value"] if c in data.columns]
    if not vars_interest:
        return pd.DataFrame({"note": ["No variables available for coverage"]}), pd.DataFrame()

    overall = data[vars_interest].notna().mean().to_frame("coverage_fraction").T.round(3)

    if "year" in data.columns:
        by_year = data.groupby("year")[vars_interest].apply(lambda x: x.notna().mean()).round(3)
    elif "ym_ts" in data.columns:
        tmp = data.copy()
        tmp["year"] = tmp["ym_ts"].dt.year
        by_year = tmp.groupby("year")[vars_interest].apply(lambda x: x.notna().mean()).round(3)
    else:
        by_year = pd.DataFrame()

    return overall, by_year

# -------------------------------------------------------------------
# LAYOUT — three tabs: Overlay, Retrospective, Data Quality
# -------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Overlay", "Retrospective", "Data Quality"])

with tab1:
    st.subheader("Overlay")
    # Woreda filter if available
    if ADM2_COL and ADM2_COL in df.columns:
        woredas = sorted(df[ADM2_COL].dropna().unique().tolist())
        sel_woredas = st.multiselect("Select woredas", woredas, default=woredas[:min(5, len(woredas))])
        # Date filter if ym_ts available
        if "ym_ts" in df.columns:
            default_range = [df["ym_ts"].min().date(), df["ym_ts"].max().date()]
            start, end = st.date_input("Date range", default_range)
            mask = (df[ADM2_COL].isin(sel_woredas)) & (df["ym_ts"].dt.date.between(start, end))
            d = df.loc[mask].copy()
        else:
            d = df[df[ADM2_COL].isin(sel_woredas)].copy()
        st.dataframe(overlay_table(d, rows=24))
    else:
        st.info("ADM2 key not available; showing pooled overlay.")
        st.dataframe(overlay_table(df, rows=24))

with tab2:
    st.subheader("Retrospective analysis")
    # Lagged correlations
    st.write("Lagged correlations (TFP vs conflict/WRSI, pooled):")
    lag_table = lagged_corr_table(df, features=("conflict_events_zone", "wrsi_value_leap"), lags=range(0, 4))
    st.dataframe(lag_table)

    # Event-study
    st.write("Event-study: Average TFP around conflict shocks (threshold >0):")
    evt_conf = event_study_table(df, feature="conflict_events_zone", target="TFP_rate_per10k",
                                 shock_type="high", threshold_value=None, window=(-1, 2))
    if evt_conf.empty:
        st.info("No valid conflict shocks found in current dataset (or target lacks variation).")
    else:
        st.dataframe(evt_conf)

    st.write("Event-study: Average TFP around WRSI low shocks (threshold below median):")
    evt_wrsi = event_study_table(df, feature="wrsi_value_leap", target="TFP_rate_per10k",
                                 shock_type="low", threshold_value=None, window=(-1, 2))
    if evt_wrsi.empty:
        st.info("No valid WRSI low shocks found in current dataset (or target lacks variation).")
    else:
        st.dataframe(evt_wrsi)

    # Honest notes based on coverage/variation
    tfp_var = df["TFP_rate_per10k"].nunique() if "TFP_rate_per10k" in df.columns else 0
    conf_var = df["conflict_events_zone"].nunique() if "conflict_events_zone" in df.columns else 0
    wrsi_var = df["wrsi_value_leap"].nunique() if "wrsi_value_leap" in df.columns else 0
    ipc_cov = df["ipc_value"].notna().mean() if "ipc_value" in df.columns else 0
    notes = []
    if tfp_var <= 1:
        notes.append("TFP is constant in this subset, so correlations/event-studies are uninformative.")
    if conf_var <= 1:
        notes.append("Conflict is constant or near-zero; inclusive shocks may yield no windows.")
    if ipc_cov == 0:
        notes.append("IPC has 0% coverage; exclude IPC from retrospective until coverage improves.")
    if notes:
        st.caption("Notes: " + " ".join(notes))
    else:
        st.caption("Retrospective signals will strengthen as coverage and variation increase.")

with tab3:
    st.subheader("Data quality")
    overall_cov, by_year_cov = coverage_tables(df)
    st.write("Overall coverage (fraction non-missing):")
    st.dataframe(overall_cov)
    st.write("Coverage by year:")
    if by_year_cov.empty:
        st.info("Yearly coverage requires a 'year' column or 'ym_ts' timestamps.")
    else:
        st.dataframe(by_year_cov)

# -------------------------------------------------------------------
# FOOTER
# -------------------------------------------------------------------
st.caption("This dashboard reflects the real integrated panel and honest retrospective outputs from the current subset. Scale-up will unlock stronger signals.")
