
# Ethiopia GAM Dashboard with Interactive Map
# This Streamlit app provides time series, summaries, and an interactive Ethiopia map heatmap.

import streamlit as st
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Mapping/geo
import geopandas as gpd
from shapely.geometry import Point
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Ethiopia GAM Dashboard", layout="wide")

@st.cache_data
def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return None

# Load data
TS_PATH = "dhis_woreda_month_timeseries.csv"
VAR_PATH = "dhis_variability_summary.csv"
RECENT_PATH = "dhis_recent12m_retrospective.csv"

# Optional geodata: You can replace this with official admin boundaries
# Attempt to read a local geojson/shapefile if provided; otherwise use a minimal placeholder
@st.cache_data
def load_geodata():
    # Try common filenames
    for cand in ["ethiopia_woreda.geojson", "ethiopia_woreda.shp", "ethiopia_admin2.geojson", "ethiopia_admin2.shp"]:
        if Path(cand).exists():
            return gpd.read_file(cand)
    return None

# DataFrames
 df_ts = load_csv(TS_PATH)
 df_var = load_csv(VAR_PATH)
 df_recent = load_csv(RECENT_PATH)
 gdf_admin = load_geodata()

st.title("Ethiopia GAM Dashboard")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    region = None
    woreda = None
    if df_recent is not None and "region" in df_recent.columns:
        regions = ["All"] + sorted([r for r in df_recent["region"].dropna().unique().tolist()])
        region = st.selectbox("Region", regions, index=0)
    if df_recent is not None and "woreda" in df_recent.columns:
        woreda_list = ["All"] + sorted([w for w in df_recent["woreda"].dropna().unique().tolist()])
        woreda = st.selectbox("Woreda", woreda_list, index=0)

    st.markdown("---")
    st.subheader("Heatmap factor")
    factor = st.selectbox(
        "Choose factor to color the map",
        [
            "GAM_prevalence",
            "MAM",
            "SAM",
            "screened_acutely_malnourished",
            "plw_screened",
            "vitamin_A_coverage",
            "deworming_coverage"
        ],
        index=0
    )

# Apply filters to the recent snapshot (assumed to hold latest values per woreda)
filtered = df_recent.copy() if df_recent is not None else None
if filtered is not None:
    if region is not None and region != "All" and "region" in filtered.columns:
        filtered = filtered[filtered["region"] == region]
    if woreda is not None and woreda != "All" and "woreda" in filtered.columns:
        filtered = filtered[filtered["woreda"] == woreda]

# Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Recent snapshot")
    if filtered is not None and not filtered.empty:
        show_cols = [c for c in filtered.columns if c.lower() in ["region", "zone", "woreda", "facility_name", "gam", "mam", "sam", "latitude", "longitude"]]
        st.dataframe(filtered[show_cols].head(20))
    else:
        st.info("Recent snapshot is not available.")

with col2:
    st.subheader("Variability summary")
    if df_var is not None and not df_var.empty:
        st.dataframe(df_var.head(20))
    else:
        st.info("Variability summary is not available.")

st.markdown("---")

# Interactive heatmap
st.subheader("Ethiopia heatmap")

# Determine factor column mapping to existing columns with best-effort guesses
col_map = {
    "GAM_prevalence": ["GAM", "gam", "gam_rate", "gam_prevalence"],
    "MAM": ["MAM", "mam"],
    "SAM": ["SAM", "sam"],
    "screened_acutely_malnourished": ["X_2017.5screened.acute.malnutrition", "screened", "screened_acutely"],
    "plw_screened": ["PLWscreened.acute.malnutrition", "plw_screened"],
    "vitamin_A_coverage": ["X6.59m.VitA.dose", "vitA_coverage"],
    "deworming_coverage": ["X24...59m.dewormed", "deworming_coverage"]
}

factor_col = None
if filtered is not None:
    for cand in col_map.get(factor, []):
        if cand in filtered.columns:
            factor_col = cand
            break

# Prepare a GeoDataFrame either from admin polygons or point lat/lon
gdf_to_plot = None
color_key = factor_col

if filtered is not None and not filtered.empty:
    if gdf_admin is not None:
        # Try fuzzy join by woreda or name
        join_key_left = None
        for c in ["woreda", "Woreda", "woreda_name", "district", "admin2_name"]:
            if c in filtered.columns:
                join_key_left = c
                break
        join_key_right = None
        for c in ["woreda", "Woreda", "NAME_2", "ADM2_EN", "admin2Name", "DIST_NAME"]:
            if c in gdf_admin.columns:
                join_key_right = c
                break
        if join_key_left is not None and join_key_right is not None:
            gdf_to_plot = gdf_admin.merge(filtered, left_on=join_key_right, right_on=join_key_left, how="left")
    if gdf_to_plot is None:
        # Fall back to points
        if "Latitude" in filtered.columns and "Longitude" in filtered.columns:
            gdf_to_plot = gpd.GeoDataFrame(
                filtered.copy(),
                geometry=gpd.points_from_xy(filtered["Longitude"], filtered["Latitude"]),
                crs="EPSG:4326"
            )

if gdf_to_plot is None or color_key is None or color_key not in (gdf_to_plot.columns if gdf_to_plot is not None else []):
    st.warning("Map cannot be rendered because required data or factor column is missing. Try a different factor or upload admin boundaries.")
else:
    # Build folium map
    center = [9.145, 40.489673]
    m = folium.Map(location=center, zoom_start=5, tiles="cartodbpositron")

    if gdf_to_plot.geometry.iloc[0].geom_type == "Polygon" or gdf_to_plot.geometry.iloc[0].geom_type == "MultiPolygon":
        # Choropleth
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
                legend_name=factor
            ).add_to(m)
        except Exception:
            # Fallback to centroid markers
            for _, r in gdf_to_plot.iterrows():
                try:
                    val = r[color_key]
                    geom = r.geometry
                    pt = geom.centroid
                    folium.CircleMarker([pt.y, pt.x], radius=6, fill=True, fill_color="red", color="red", popup=str(val)).add_to(m)
                except Exception:
                    pass
    else:
        # Points layer
        # Normalize color intensity by quantiles
        vals = gdf_to_plot[color_key].astype(float)
        q = np.nanquantile(vals, [0.1, 0.5, 0.9]) if np.isfinite(vals).any() else [0, 0, 0]
        def color_for(v):
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
            val = r[color_key]
            folium.CircleMarker([lat, lon], radius=6, fill=True, fill_color=color_for(val), color=color_for(val), popup=str(val)).add_to(m)

    st_folium(m, height=600, width=None)

st.markdown("---")

st.caption("Notes: If the administrative boundary file is not present, the app will fall back to plotting facility or woreda points using latitude/longitude in the recent snapshot. You can add an Ethiopia admin2 GeoJSON named ethiopia_woreda.geojson to enable choropleth.")
