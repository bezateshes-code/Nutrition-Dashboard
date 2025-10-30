# dashboard_chart.py
import pandas as pd
import plotly.express as px
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# -----------------------------
# Page setup
st.set_page_config(page_title="Ethiopia Malnutrition Dashboard", layout="wide")
st.title("📊 Ethiopia Acute Malnutrition Dashboard")

# -----------------------------
# Data source for trends
CSV_TRENDS = "https://raw.githubusercontent.com/bezateshes-code/Nutrition-Dashboard/refs/heads/main/agg_df_variability_and_forecasts_full_table%20(1).csv"

@st.cache_data
def load_trend_data():
    return pd.read_csv(CSV_TRENDS, parse_dates=["date"])

df = load_trend_data()

# -----------------------------
# Sidebar filters
regions = st.sidebar.multiselect(
    "Select Region(s)", options=df['region'].unique(), default=df['region'].unique()
)
woredas = st.sidebar.multiselect(
    "Select Woreda(s)", options=df['woreda'].unique(),
    default=["beyeda","debark_town","janamora","east_imi","west_imi"]
)
metric = st.sidebar.radio("Select Metric", ["Acute Cases", "Variability Factor"])

# -----------------------------
# Tabs
tab1, tab2 = st.tabs(["📈 Trends", "🗺 Forecast Map"])

with tab1:
    # Filtered data
    df_filtered = df[(df['region'].isin(regions)) & (df['woreda'].isin(woredas))]

    # Choose y-axis
    if metric == "Acute Cases":
        y_col = "acute_cases"
        y_title = "Acute Malnutrition Cases"
    else:
        y_col = "variability_factor"
        y_title = "Variability (CV)"

    # Plot
    fig = px.line(
        df_filtered,
        x="date",
        y=y_col,
        color="woreda",
        facet_col="woreda",
        facet_col_wrap=3,
        title=f"{y_title} Over Time",
        markers=True
    )

    # Add CV=1 threshold line if variability selected
    if metric == "Variability Factor":
        fig.add_hline(y=1, line_dash="dot", line_color="gray")

    fig.update_layout(height=600, width=1000, showlegend=False, title_x=0.5)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📊 Ethiopia Forecast Heatmap (Nov–Dec 2025)")

    # -----------------------------
    # Data sources
    CSV_URL = "https://github.com/bezateshes-code/Nutrition-Dashboard/raw/e4aae170a9cb811bb28bd1631057b50c9b74d5c6/forecasts_woreda_2025_11_12.csv"
    GEOJSON_URL = "https://raw.githubusercontent.com/bezateshes-code/Nutrition-Dashboard/main/eth_admbnda_adm3_2025_simplified.geojson"

    # Load data
    df_forecast = pd.read_csv(CSV_URL)
    gdf = gpd.read_file(GEOJSON_URL)

    # Normalize helper
    def norm_name(s):
        return (
            s.astype(str)
             .str.lower()
             .str.strip()
             .str.replace(r"[^\w\s]", "", regex=True)
             .str.replace(r"\s+", "_", regex=True)
        )

    NAME_MAP = {
        "debark town": "debark_town",
        "debark_town": "debark_town",
        "east imi": "east_imi",
        "west imi": "west_imi",
        "beyeda": "beyeda",
        "janamora": "janamora",
    }

    # Clean forecast data
    df_forecast["woreda_norm"] = norm_name(df_forecast["woreda"]).replace(NAME_MAP)
    df_snapshot = df_forecast.groupby("woreda_norm", as_index=False)["forecast"].sum()

    # Clean shapefile
    gdf["woreda_norm"] = norm_name(gdf["admin3Name"]).replace(NAME_MAP)

    # Merge and filter only matched woredas
    gdf_to_plot = gdf.merge(df_snapshot, on="woreda_norm", how="inner")
    gdf_for_map = gdf_to_plot[["woreda_norm", "forecast", "geometry"]].copy()

    if gdf_for_map.empty:
        st.warning("No matching woredas found between forecast CSV and shapefile.")
    else:
        # Center map on Ethiopia
        m = folium.Map(location=[9.145, 40.4897], zoom_start=6, tiles="cartodbpositron")

        # Choropleth shading
        choropleth = folium.Choropleth(
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

        # Hover tooltips
        folium.GeoJsonTooltip(
            fields=["woreda_norm", "forecast"],
            aliases=["Woreda:", "Forecast:"],
            localize=True
        ).add_to(choropleth.geojson)

        # Bubble markers at centroids
        for _, row in gdf_for_map.iterrows():
            if pd.notna(row["forecast"]):
                lat, lon = row["geometry"].centroid.y, row["geometry"].centroid.x
                folium.CircleMarker(
                    [lat, lon],
                    radius=max(4, min(20, row["forecast"]/50)),
                    fill=True,
                    fill_color="blue",
                    color="blue",
                    popup=f"{row['woreda_norm'].title()}: {row['forecast']:.0f}"
                ).add_to(m)

        # Display map in Streamlit
        st_folium(m, height=600, width="stretch")

        # Data table
        st.subheader("Matched Woredas Forecast Data")
        st.dataframe(
            gdf_for_map[["woreda_norm", "forecast"]]
            .sort_values("forecast", ascending=False)
            .reset_index(drop=True)
            .rename(columns={"woreda_norm": "Woreda", "forecast": "Forecasted Cases"})
        )
# streamlit run dashboard_chart.py
#