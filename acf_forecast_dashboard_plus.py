import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Ethiopia Forecast Map", layout="wide")
st.title("📊 Ethiopia Forecast Heatmap (Nov–Dec 2025)")

# -----------------------------
# GitHub raw URLs
CSV_URL = "https://github.com/bezateshes-code/Nutrition-Dashboard/raw/e4aae170a9cb811bb28bd1631057b50c9b74d5c6/forecasts_woreda_2025_11_12.csv"
df_forecast = pd.read_csv(CSV_URL)
GEOJSON_URL = "https://raw.githubusercontent.com/bezateshes-code/Nutrition-Dashboard/main/eth_admbnda_adm3_2025_simplified.geojson"

# Load forecast CSV
df_forecast = pd.read_csv(CSV_URL)

# Load GeoJSON
gdf = gpd.read_file(GEOJSON_URL)

# -----------------------------
# Normalize helper
def norm_name(s):
    return (
        s.astype(str)
         .str.lower()
         .str.strip()
         .str.replace(r"[^\w\s]", "", regex=True)
         .str.replace(r"\s+", "_", regex=True)
    )

# Correction map
NAME_MAP = {
    "debark town": "debark_town",
    "debark_town": "debark_town",
    "east imi": "east_imi",
    "west imi": "west_imi",
    "beyeda": "beyeda",
    "janamora": "janamora",
}

# -----------------------------
# Clean forecast data
df_forecast["woreda_norm"] = norm_name(df_forecast["woreda"]).replace(NAME_MAP)
df_snapshot = df_forecast.groupby("woreda_norm", as_index=False)["forecast"].sum()

# Clean GeoJSON
gdf["woreda_norm"] = norm_name(gdf["admin3Name"]).replace(NAME_MAP)

# Merge
gdf_to_plot = gdf.merge(df_snapshot, on="woreda_norm", how="left")

# Keep only necessary columns
gdf_for_map = gdf_to_plot[["woreda_norm", "forecast", "geometry"]].copy()

# -----------------------------
# Render map
m = folium.Map(location=[9.145, 40.4897], zoom_start=6, tiles="cartodbpositron")
folium.Choropleth(
    geo_data=gdf_for_map,
    data=gdf_for_map,
    columns=["woreda_norm", "forecast"],
    key_on="feature.properties.woreda_norm",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    nan_fill_color="#dddddd",
    legend_name="Forecasted acute cases (Nov–Dec 2025)"
).add_to(m)

st_folium(m, height=600, width="stretch")

# -----------------------------
# Debug table
st.subheader("Merged Data Preview")
st.dataframe(gdf_for_map[["woreda_norm", "forecast"]])


##  python -m streamlit run acf_forecast_Map_dashboard.py