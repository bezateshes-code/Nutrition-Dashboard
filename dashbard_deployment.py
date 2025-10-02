# Save this as 05_dashboard_deployment.py and run with: streamlit run 05_dashboard_deployment.py

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# -------------------------------
# 1. Load Feature Panel
# -------------------------------
df = pd.read_parquet("woreda_month_features.parquet")

st.title("📊 Nutrition & Climate Dashboard")
st.markdown("Interactive QC and trends for **GAM, MAM, SAM** with climate overlays.")

# -------------------------------
# 2. Sidebar Filters
# -------------------------------
woredas = df["woreda_key"].unique()
selected_woreda = st.sidebar.selectbox("Select Woreda", sorted(woredas))
date_range = st.sidebar.slider(
    "Select Month Range",
    min_value=df["ym"].min().to_pydatetime(),
    max_value=df["ym"].max().to_pydatetime(),
    value=(df["ym"].min().to_pydatetime(), df["ym"].max().to_pydatetime()),
    format="YYYY-MM"
)

mask = (df["woreda_key"] == selected_woreda) & (df["ym"].between(date_range[0], date_range[1]))
subset = df.loc[mask]

# -------------------------------
# 3. Line Charts: GAM, MAM, SAM
# -------------------------------
st.subheader(f"Nutrition Trends for {selected_woreda}")
fig, ax = plt.subplots(figsize=(10,4))
for col in ["GAM","MAM","SAM"]:
    sns.lineplot(data=subset, x="ym", y=col, label=col, ax=ax)
ax.set_ylabel("Cases")
ax.set_xlabel("Month")
st.pyplot(fig)

# -------------------------------
# 4. Bar Charts: QC Flags
# -------------------------------
st.subheader("QC Flags by Woreda")

low_rep = df.groupby("woreda_key")["low_reporting"].sum().reset_index()
low_clim = df.groupby("woreda_key")["low_climate_coverage"].sum().reset_index()

col1, col2 = st.columns(2)
with col1:
    st.bar_chart(low_rep.set_index("woreda_key"))
    st.caption("Months with Low Reporting")
with col2:
    st.bar_chart(low_clim.set_index("woreda_key"))
    st.caption("Months with Low Climate Coverage")

# -------------------------------
# 5. Interactive Map: Avg GAM
# -------------------------------
st.subheader("Average GAM by Woreda")

avg_gam = df.groupby("woreda_key", as_index=False)["GAM"].mean()

# Dummy coordinates for centering Ethiopia (replace with shapefile join if available)
m = folium.Map(location=[9.0, 39.0], zoom_start=6)
for _, row in avg_gam.iterrows():
    folium.CircleMarker(
        location=[9.0, 39.0],  # placeholder, replace with woreda centroid
        radius=5,
        popup=f"{row['woreda_key']}: {row['GAM']:.2f}",
        color="red",
        fill=True
    ).add_to(m)

st_folium(m, width=700, height=450)
