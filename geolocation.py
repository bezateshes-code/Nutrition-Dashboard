import geopandas as gpd

# --- Step 1: Point this to your local shapefile (inside the unzipped folder)
# Example: "C:/Users/PC/Downloads/ethiopia_woreda/ETH_adm3_woreda.shp"
shapefile_path = r"D:/VS/Eth_Woreda_2013.shp"

# --- Step 2: Read the shapefile
gdf = gpd.read_file(shapefile_path)

# --- Step 3: Save as GeoJSON
output_path = "D:/VS/ethiopia_woredas.geojson"
gdf.to_file(output_path, driver="GeoJSON")

print(f"✅ Saved GeoJSON to {output_path}")
