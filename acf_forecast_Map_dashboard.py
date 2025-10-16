# acf_forecast_Map_dashboard.py
import streamlit as st
import pandas as pd
import geopandas as gpd
import io
import math
import altair as alt
from streamlit_folium import st_folium
import folium
from pathlib import Path
from io import StringIO
import numpy as np

# -----------------------------
# Configuration and theme
AAH_BLUE = "#0072CE"
AAH_GREEN = "#78BE20"
AAH_ORANGE = "#F58220"
AAH_GREY = "#4D4D4D"

st.set_page_config(page_title="Action Against Hunger – Ethiopia Forecast Dashboard", layout="wide")

# -----------------------------
# Utilities
def norm_name_series(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.lower()
         .str.strip()
         .str.replace(r"[^\w\s]","", regex=True)
         .str.replace(r"\s+","_", regex=True)
    )

NAME_MAP = {"debark_town": "debark"}  # extend if you find more mismatches

@st.cache_data
def load_optional_csv(path: str):
    p = Path(path)
    if p.exists():
        try:
            return pd.read_csv(p)
        except Exception:
            return None
    return None

@st.cache_data
def load_geojson(path: str):
    p = Path(path)
    if p.exists():
        try:
            return gpd.read_file(p)
        except Exception:
            return None
    return None

@st.cache_data
def load_geojson_from_url(url: str):
    try:
        return gpd.read_file(url)
    except Exception:
        return None

# -----------------------------
# Paths and defaults
TS_PATH = "dhis_woreda_month_timeseries.csv"
VAR_PATH = "dhis_variability_summary.csv"
RECENT_PATH = "dhis_recent12m_retrospective.csv"
GEO_PATH_LOCAL = "ethiopia_woreda.geojson"
GEOJSON_RAW_URL = "https://raw.githubusercontent.com/bezateshes-code/Nutrition-Dashboard/main/ethiopia_woredas.geojson"

# Embedded fallback sample timeseries
SAMPLE_CSV = """region,woreda,date,acute_cases
amhara,beyeda,2022-07-01,467
amhara,beyeda,2023-07-01,120
amhara,beyeda,2024-07-01,0
amhara,debark_town,2022-07-01,180
amhara,debark_town,2023-07-01,90
amhara,debark_town,2024-07-01,0
amhara,janamora,2022-07-01,3044
amhara,janamora,2023-07-01,2800
amhara,janamora,2024-07-01,3100
somali,east_imi,2022-07-01,88
somali,east_imi,2023-07-01,3400
somali,east_imi,2024-07-01,3200
somali,west_imi,2022-07-01,336
somali,west_imi,2023-07-01,400
somali,west_imi,2024-07-01,0
"""

# -----------------------------
# Load data (CSV)
df_ts = load_optional_csv(TS_PATH)
df_var = load_optional_csv(VAR_PATH)
df_recent = load_optional_csv(RECENT_PATH)
gdf_admin_local = load_geojson(GEO_PATH_LOCAL)

if df_ts is None:
    df_ts = pd.read_csv(StringIO(SAMPLE_CSV))

# Basic cleaning for timeseries
df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
df_ts["acute_cases"] = pd.to_numeric(df_ts.get("acute_cases", 0), errors="coerce").fillna(0).astype(float)
df_ts["woreda"] = norm_name_series(df_ts.get("woreda", pd.Series(""))).map(lambda x: NAME_MAP.get(x, x))
df_ts["region"] = norm_name_series(df_ts.get("region", pd.Series("")))
df_ts["date_only"] = df_ts["date"].dt.date

if df_recent is not None:
    df_recent["woreda"] = norm_name_series(df_recent.get("woreda", pd.Series(""))).map(lambda x: NAME_MAP.get(x, x))
    df_recent["region"] = norm_name_series(df_recent.get("region", pd.Series("")))

# -----------------------------
# Sidebar & header
st.markdown(
    f"""
    <div style="display:flex; align-items:center; background-color:{AAH_BLUE}; padding:12px;">
        <div style="width:10px; height:40px; background-color:{AAH_GREEN}; margin-right:12px;"></div>
        <h2 style="color:white; margin:0;">Action Against Hunger – Ethiopia Forecast Dashboard</h2>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.header("Controls")
st.sidebar.markdown("Choose data and filters for the dashboard.")

use_embedded = st.sidebar.checkbox("Use embedded sample (ignore CSV file)", value=False)
if use_embedded:
    df_ts = pd.read_csv(StringIO(SAMPLE_CSV))
    df_ts["date"] = pd.to_datetime(df_ts["date"])
    df_ts["acute_cases"] = pd.to_numeric(df_ts["acute_cases"], errors="coerce").fillna(0)

uploaded_csv = st.sidebar.file_uploader("Upload timeseries CSV (optional)", type=["csv"])
if uploaded_csv is not None:
    try:
        df_ts = pd.read_csv(uploaded_csv)
        df_ts["date"] = pd.to_datetime(df_ts["date"], errors="coerce")
        df_ts["acute_cases"] = pd.to_numeric(df_ts.get("acute_cases", 0), errors="coerce").fillna(0)
        df_ts["woreda"] = norm_name_series(df_ts.get("woreda", pd.Series(""))).map(lambda x: NAME_MAP.get(x, x))
        df_ts["region"] = norm_name_series(df_ts.get("region", pd.Series("")))
        df_ts["date_only"] = df_ts["date"].dt.date
        st.sidebar.success("Uploaded CSV loaded.")
    except Exception as e:
        st.sidebar.error("Failed to read uploaded CSV: " + str(e))

# GeoJSON: try GitHub raw first, then local, then allow upload
gdf_admin = None
geo_msg = None
try:
    gdf_admin = load_geojson_from_url(GEOJSON_RAW_URL)
    if gdf_admin is not None:
        st.sidebar.success(f"Loaded admin GeoJSON from GitHub ({len(gdf_admin)} features)")
    else:
        if gdf_admin_local is not None:
            gdf_admin = gdf_admin_local
            st.sidebar.success(f"Loaded local GeoJSON ({len(gdf_admin)} features)")
        else:
            geo_msg = "No admin GeoJSON loaded from GitHub or local file."
except Exception as e:
    geo_msg = f"GeoJSON load failed: {e}"

geo_upload = st.sidebar.file_uploader("Upload admin GeoJSON (optional)", type=["geojson", "json"])
if geo_upload is not None:
    try:
        gdf_admin = gpd.read_file(geo_upload)
        st.sidebar.success("Uploaded GeoJSON loaded")
    except Exception as e:
        st.sidebar.error("Failed to read uploaded GeoJSON: " + str(e))

if geo_msg:
    st.sidebar.info(geo_msg)

# -----------------------------
# Filters
regions = ["All"] + sorted(df_ts["region"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("Region", regions, index=0)

if region_sel == "All":
    woptions = ["All"] + sorted(df_ts["woreda"].dropna().unique().tolist())
else:
    woptions = ["All"] + sorted(df_ts.loc[df_ts["region"] == region_sel, "woreda"].dropna().unique().tolist())
woreda_sel = st.sidebar.selectbox("Woreda", woptions, index=0)

date_min = df_ts["date"].min().date()
date_max = df_ts["date"].max().date()
st.sidebar.markdown("### Date range")
date_left = st.sidebar.date_input("Start date", value=date_min, min_value=date_min, max_value=date_max)
date_right = st.sidebar.date_input("End date", value=date_max, min_value=date_min, max_value=date_max)
if date_left > date_right:
    date_left, date_right = date_right, date_left

# -----------------------------
# Apply filters
mask = (df_ts["date_only"] >= date_left) & (df_ts["date_only"] <= date_right)
if region_sel != "All":
    mask &= (df_ts["region"] == region_sel)
if woreda_sel != "All":
    mask &= (df_ts["woreda"] == woreda_sel)
df_filt = df_ts.loc[mask].copy()

# compute roll3 for plotting clarity
if "acute_cases" in df_filt.columns:
    df_filt["acute_cases"] = pd.to_numeric(df_filt["acute_cases"], errors="coerce").fillna(0)
    df_filt = df_filt.sort_values(["woreda", "date"])
    df_filt["roll3"] = df_filt.groupby("woreda")["acute_cases"].transform(lambda s: s.rolling(3, min_periods=1).mean())
else:
    df_filt["roll3"] = np.nan

# prepare recent snapshot
df_recent = None
if "date" in df_filt.columns and "woreda" in df_filt.columns and not df_filt.empty:
    last_date = df_filt["date"].max()
    df_recent = df_filt[df_filt["date"] == last_date].copy()

# -----------------------------
# Tabs
tab1, tab2 = st.tabs(["📊 Charts", "🗺️ Map"])

# -----------------------------
# Tab 1: Charts (improved)
with tab1:
    st.markdown("#### Overview")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Records", str(len(df_filt)))
    with c2:
        total_cases = int(df_filt["acute_cases"].sum()) if not df_filt.empty else 0
        st.metric("Total acute cases", f"{total_cases:,}")
    with c3:
        st.metric("Regions", str(df_filt["region"].nunique()))
    with c4:
        st.metric("Woredas", str(df_filt["woreda"].nunique()))

    st.markdown("---")

    # Chart controls
    st.subheader("Acute cases over time")
    chart_view = st.radio("Chart view", ["Top N overlay (cleaned)", "Small multiples"], index=0)
    top_n = st.slider("Top N woredas (by peak)", min_value=1, max_value=min(30, max(1, df_filt["woreda"].nunique() if "woreda" in df_filt.columns else 1)), value=min(6, max(1, df_filt["woreda"].nunique() if "woreda" in df_filt.columns else 1)))

    if df_filt.empty or not {"date", "woreda", "acute_cases"}.issubset(df_filt.columns):
        st.info("No data for the selected filters and date range.")
    else:
        # compute top woredas by raw peak
        top_w = df_filt.groupby("woreda")["acute_cases"].max().nlargest(top_n).index.tolist()
        df_top = df_filt[df_filt["woreda"].isin(top_w)].copy()

        # color palette (color-blind friendly)
        palette = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#F0E442", "#56B4E9", "#E69F00", "#000000", "#999999"]
        unique_w = sorted(df_top["woreda"].unique())
        color_scale = alt.Scale(domain=unique_w, range=palette[: max(1, len(unique_w))])

        if chart_view == "Top N overlay (cleaned)":
            select = alt.selection_point(fields=["woreda"], empty=False)
            base = alt.Chart(df_top).encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("roll3:Q", title="Acute cases (3-mo mean)"),
                color=alt.Color("woreda:N", scale=color_scale, legend=alt.Legend(title="Woreda")),
                tooltip=["region", "woreda", "date:T", "acute_cases:Q", "roll3:Q"]
            )
            lines = base.mark_line(strokeWidth=2.6).encode(opacity=alt.condition(select, alt.value(1), alt.value(0.15)))
            points = base.mark_point(size=25, filled=True).encode(opacity=alt.condition(select, alt.value(0.9), alt.value(0.08)))
            last_label = alt.Chart(df_top).transform_window(last_date="max(date)", groupby=["woreda"]).transform_filter("datum.date == datum.last_date").mark_text(align="left", dx=6, dy=-5, fontSize=11).encode(x="date:T", y=alt.Y("roll3:Q"), text=alt.Text("woreda:N"), color=alt.Color("woreda:N", scale=color_scale))
            chart = (lines + points + last_label).add_params(select).properties(height=460, width="container")
            st.altair_chart(chart, use_container_width=True)
        else:
            # small multiples: one row per woreda (vertical) ensure consistent y scale
            y_max = df_top["roll3"].max()
            facet = (alt.Chart(df_top).mark_line(point=False).encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("roll3:Q", title="Acute cases (3-mo mean)", scale=alt.Scale(domain=[0, max(y_max, 1)])),
                color=alt.Color("woreda:N", legend=None),
                tooltip=["region", "woreda", "date:T", "acute_cases:Q", "roll3:Q"]
            ).properties(height=120)).facet(row=alt.Row("woreda:N", title=None, header=alt.Header(labelFontSize=11)))
            st.altair_chart(facet, use_container_width=True)

        # Top peaks summary
        peaks = df_top.groupby("woreda")["acute_cases"].max().sort_values(ascending=False)
        peak_display = "; ".join([f"{w}: {int(v)}" for w, v in peaks.items()])
        st.markdown("**Top peaks in view:** " + peak_display)

    st.markdown("---")
    st.subheader("Heatmap views")
    st.caption("Geographic bubble heatmap (approximate centroids) and matrix heatmap")

    woreda_coords = {
        "beyeda": {"lat": 13.31, "lon": 38.42},
        "debark": {"lat": 13.15, "lon": 37.90},
        "janamora": {"lat": 13.25, "lon": 38.15},
        "east_imi": {"lat": 6.48, "lon": 42.19},
        "west_imi": {"lat": 6.25, "lon": 42.62},
    }

    geo_df = (
        df_filt.groupby(["region", "woreda"], as_index=False)["acute_cases"].sum()
        .assign(
            lat=lambda d: d["woreda"].map(lambda w: woreda_coords.get(str(w).lower(), {}).get("lat", math.nan)),
            lon=lambda d: d["woreda"].map(lambda w: woreda_coords.get(str(w).lower(), {}).get("lon", math.nan))
        )
    )

    st.markdown("##### Geographic bubble heatmap (embedded centroids)")
    if geo_df[["lat", "lon"]].dropna().empty:
        st.caption("No coordinates available for selected woredas.")
    else:
        bubble = (
            alt.Chart(geo_df.dropna(subset=["lat", "lon"]))
            .mark_circle()
            .encode(
                longitude="lon:Q",
                latitude="lat:Q",
                size=alt.Size("acute_cases:Q", title="Acute cases", scale=alt.Scale(range=[100, 3000])),
                color=alt.Color("region:N", scale=alt.Scale(range=[AAH_BLUE, AAH_ORANGE, AAH_GREEN])),
                tooltip=["region", "woreda", "acute_cases:Q"]
            )
            .project(type="mercator")
            .properties(height=420)
        )
        st.altair_chart(bubble, use_container_width=True)

    st.markdown("##### Matrix heatmap (region × woreda)")
    mat_df = df_filt.groupby(["region", "woreda"], as_index=False)["acute_cases"].sum()
    if mat_df.empty:
        st.caption("No data to show.")
    else:
        matrix = (
            alt.Chart(mat_df)
            .mark_rect()
            .encode(
                x=alt.X("woreda:N", title="Woreda"),
                y=alt.Y("region:N", title="Region"),
                color=alt.Color("acute_cases:Q", title="Acute cases", scale=alt.Scale(scheme="oranges")),
                tooltip=["region", "woreda", "acute_cases:Q"]
            )
            .properties(height=260)
        )
        st.altair_chart(matrix, use_container_width=True)

    st.markdown("---")
    st.subheader("Filtered data")
    st.dataframe(df_filt.drop(columns=["date_only"], errors="ignore"), use_container_width=True)

    st.download_button(
        "Download filtered CSV",
        data=df_filt.drop(columns=["date_only"], errors="ignore").to_csv(index=False).encode("utf-8"),
        file_name="filtered_summary_forecast.csv",
        mime="text/csv"
    )

    st.markdown(
        f"""
        <div style="text-align:center; color:{AAH_GREY}; font-size:0.9em; margin-top:16px;">
            © Action Against Hunger – Ethiopia Dashboard
        </div>
        """,
        unsafe_allow_html=True
    )
# -----------------------------
# Tab 2: Map
with tab2:
    st.subheader("Ethiopia heatmap")
    # Choose factor for map: fallback to acute_cases if recent snapshot missing
    map_factor = None
    if df_recent is not None:
        # best-effort mapping to commonly named columns
        cand_cols = ["GAM_prevalence", "gam", "GAM", "MAM", "SAM", "screened_acutely_malnourished", "plw_screened", "vitamin_A_coverage"]
        for c in cand_cols:
            if c in df_recent.columns:
                map_factor = c
                break

    if map_factor is None and "acute_cases" in df_filt.columns:
        # create a recent snapshot from df_filt aggregated by woreda
        df_snapshot = df_filt.groupby("woreda", as_index=False)["acute_cases"].sum()
        df_snapshot = df_snapshot.rename(columns={"acute_cases": "acute_cases_snapshot"})
        map_factor = "acute_cases_snapshot"
    else:
        df_snapshot = df_recent.copy() if df_recent is not None else None

    # Prepare GeoDataFrame to plot
    gdf_to_plot = None
    color_key = map_factor

    if df_snapshot is not None:
        if gdf_admin is not None:
            # attempt fuzzy join using best candidate keys
            left_key = None
            for c in ["woreda", "Woreda", "woreda_name", "district", "admin2_name"]:
                if c in df_snapshot.columns:
                    left_key = c
                    break
            right_key = None
            for c in ["woreda", "Woreda", "NAME_2", "ADM2_EN", "admin2Name", "DIST_NAME", "WOREDANAME"]:
                if c in gdf_admin.columns:
                    right_key = c
                    break
            if left_key and right_key:
                gdf_admin_copy = gdf_admin.copy()
                gdf_admin_copy[right_key] = norm_name_series(gdf_admin_copy[right_key].astype(str)).map(lambda x: NAME_MAP.get(x, x))
                df_snapshot_copy = df_snapshot.copy()
                if left_key in df_snapshot_copy.columns:
                    df_snapshot_copy[left_key] = norm_name_series(df_snapshot_copy[left_key].astype(str)).map(lambda x: NAME_MAP.get(x, x))
                try:
                    gdf_to_plot = gdf_admin_copy.merge(df_snapshot_copy, left_on=right_key, right_on=left_key, how="left")
                except Exception:
                    gdf_to_plot = None
        # fallback to point plotting if lat/lon present
        if gdf_to_plot is None and {"latitude", "longitude", "lat", "lon", "Latitude", "Longitude"}.intersection(set(df_snapshot.columns)):
            lat_col = next((c for c in df_snapshot.columns if c.lower() in ["latitude", "lat"]), None)
            lon_col = next((c for c in df_snapshot.columns if c.lower() in ["longitude", "lon"]), None)
            if lat_col and lon_col:
                gdf_to_plot = gpd.GeoDataFrame(
                    df_snapshot.copy(),
                    geometry=gpd.points_from_xy(df_snapshot[lon_col], df_snapshot[lat_col]),
                    crs="EPSG:4326"
                )

    if gdf_to_plot is None or color_key not in (gdf_to_plot.columns if gdf_to_plot is not None else []):
        st.warning("Map cannot be rendered because administrative boundaries or required factor column are missing. Add ethiopia_woreda.geojson or include lat/lon in the recent snapshot.")
    else:
        m = folium.Map(location=[9.145, 40.489673], zoom_start=6, tiles="cartodbpositron")
        first_geom = gdf_to_plot.geometry.iloc[0]
        if first_geom.geom_type in ["Polygon", "MultiPolygon"]:
            try:
                gjson = gdf_to_plot.to_json()
                folium.Choropleth(
                    geo_data=gjson,
                    data=gdf_to_plot,
                    columns=[gdf_to_plot.columns[0], color_key],
                    key_on="feature.properties." + gdf_to_plot.columns[0],
                    fill_color="YlOrRd",
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    nan_fill_color="#dddddd",
                    legend_name=map_factor
                ).add_to(m)
            except Exception:
                # fallback: centroid markers
                for _, r in gdf_to_plot.iterrows():
                    try:
                        val = r.get(color_key, None)
                        pt = r.geometry.centroid
                        folium.CircleMarker([pt.y, pt.x], radius=6, fill=True, fill_color="red", color="red", popup=str(val)).add_to(m)
                    except Exception:
                        pass
        else:
            # points
            vals = pd.to_numeric(gdf_to_plot[color_key], errors="coerce")
            q = pd.Series(vals).quantile([0.1, 0.5, 0.9]).values if not vals.isna().all() else [0, 0, 0]
            def color_for(v):
                try:
                    v = float(v)
                except Exception:
                    return "#bdbdbd"
                if pd.isna(v):
                    return "#bdbdbd"
                if v <= q[0]:
                    return "#ffffb2"
                if v <= q[1]:
                    return "#fecc5c"
                if v <= q[2]:
                    return "#fd8d3c"
                return "#e31a1c"
            for _, r in gdf_to_plot.iterrows():
                lat = r.geometry.y
                lon = r.geometry.x
                val = r.get(color_key, None)
                folium.CircleMarker([lat, lon], radius=6, fill=True, fill_color=color_for(val), color=color_for(val), popup=str(val)).add_to(m)

        st_folium(m, height=600, width="stretch")

st.markdown("---")
st.caption("Notes: keep zeros in your source timeseries; they represent real zero reports. Provide ethiopia_woreda.geojson (admin2) to enable choropleth plotting.")

#  python -m streamlit run acf_forecast_Map_dashboard.py
# cd "D:/VS/ethiopia_gam_dashboard"