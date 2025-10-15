import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import io

# -----------------------------
# Embedded CSV data (expand with your full dataset)
CSV_DATA = """region,woreda,date,acute_cases
amhara,beyeda,7/1/2022,467
amhara,debark_town,7/1/2022,180
amhara,janamora,7/1/2022,3044
somali,east_imi,7/1/2022,88
somali,west_imi,7/1/2022,336
"""

df = pd.read_csv(io.StringIO(CSV_DATA))
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# -----------------------------
# Fetch Ethiopia GeoJSON from GitHub (replace with your actual repo path)
url = "https://raw.githubusercontent.com/<your-username>/<your-repo>/main/ethiopia_woredas.geojson"
ethiopia = gpd.read_file(url)

# -----------------------------
# Normalize names for join
ethiopia["woreda"] = ethiopia["woreda"].str.lower().str.replace(" ", "_")
df_latest = df.groupby("woreda", as_index=False)["acute_cases"].sum()
df_latest["woreda"] = df_latest["woreda"].str.lower().str.replace(" ", "_")

# -----------------------------
# Merge data with polygons
merged = ethiopia.merge(df_latest, on="woreda", how="left")

# -----------------------------
# Folium choropleth
m = folium.Map(location=[9.145, 40.4897], zoom_start=6)

folium.Choropleth(
    geo_data=merged,
    data=merged,
    columns=["woreda", "acute_cases"],
    key_on="feature.properties.woreda",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Acute Cases"
).add_to(m)

folium.GeoJson(
    merged,
    tooltip=folium.GeoJsonTooltip(fields=["woreda", "acute_cases"])
).add_to(m)

# -----------------------------
# Streamlit display
st.title("Ethiopia Acute Malnutrition Heatmap")
st_folium(m, width=800, height=500)

#  python -m streamlit run acf_forecast_dashboard.py
# cd "D:/VS/ethiopia_gam_dashboard"  
