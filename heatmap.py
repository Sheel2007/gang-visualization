import pandas as pd
import folium
import json
import os
import numpy as np

# --- Configuration ---
file_path = 'Cook County Regional Gang Intelligence Database.xlsx'
column_zip = 'address_zip'
column_race = 'Subject_Race_ID'

# URL for a publicly available GeoJSON file covering Chicago ZIP codes
# NOTE: Using a public URL for demonstration. In a real-world scenario, you may need 
# to acquire a precise GeoJSON for all Cook County ZIPs (e.g., from the county GIS site).
GEOJSON_URL = 'https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/il_illinois_zip_codes_geo.min.json'
OUTPUT_MAP_FILE = 'index.html'


# --- 1. Data Loading ---
print(f"Attempting to read data from: {file_path}")

try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    print(f"\nERROR: The file '{file_path}' was not found.")
    print("Please ensure the Excel file is in the same directory as this script.")
    print("--- Generating sample data for demonstration instead ---")
    
    # Fallback: Generate sample data for demonstration
    np.random.seed(42)
    data_size = 5000
    
    # Simulate a pattern where certain races cluster in certain ZIPs
    # Using real Chicago area ZIPs that exist in the GeoJSON data for better demonstration
    real_zips = [60601, 60608, 60616, 60617, 60620, 60632, 60640, 60649, 60653, 60827]
    zips = np.random.choice(real_zips, size=data_size)
    races = []
    for z in zips:
        if z in [60620, 60649]: races.append(np.random.choice(['Black', 'Hispanic', 'White'], p=[0.7, 0.2, 0.1]))
        elif z in [60608, 60632]: races.append(np.random.choice(['Hispanic', 'White', 'Black'], p=[0.6, 0.3, 0.1]))
        else: races.append(np.random.choice(['White', 'Black', 'Hispanic'], p=[0.4, 0.3, 0.3]))

    df = pd.DataFrame({
        column_zip: zips,
        column_race: races
    })
    
except Exception as e:
    print(f"\nAn unexpected error occurred during file reading: {e}")
    exit()

# Check if required columns exist
if column_zip not in df.columns or column_race not in df.columns:
    print("\nERROR: One or both required columns were not found in the Excel file.")
    print(f"Expected columns: '{column_zip}' and '{column_race}'")
    print(f"Available columns: {list(df.columns)}")
    exit()

print(f"Data loaded successfully. Total records: {len(df)}")


# --- 2. Data Cleaning and Aggregation ---

# Clean up ZIP code: ensure it's a 5-digit string key
df[column_zip] = df[column_zip].astype(str).str.replace(r'\..*', '', regex=True).str.strip().str[:5]
df = df[df[column_zip].str.len() == 5]

# Clean up Race column: handle missing values
df[column_race] = df[column_race].astype(str).str.strip().str.replace('NULL', 'Unknown', case=False).fillna('Unknown').replace('nan', 'Unknown')

# Create the contingency table (Counts of Race per ZIP)
# Index = ZIP, Columns = Race
race_zip_counts = pd.crosstab(df[column_zip], df[column_race])

# Calculate the percentage concentration of each race WITHIN that ZIP code (row sum is 100%)
race_zip_percentage = race_zip_counts.div(race_zip_counts.sum(axis=1), axis=0) * 100

# Find the DOMINANT race and its percentage for each ZIP code
dominant_race = race_zip_percentage.idxmax(axis=1).rename('Dominant_Race')
dominant_percentage = race_zip_percentage.max(axis=1).rename('Dominant_Percentage')
total_records = race_zip_counts.sum(axis=1).rename('Total_Records')

# Combine the results into a final DataFrame for mapping
map_data = pd.concat([dominant_race, dominant_percentage, total_records], axis=1)
map_data = map_data.reset_index()

# Filter to only the ZIP codes present in our data
map_data = map_data[map_data[column_zip].isin(df[column_zip].unique())]


# --- 3. Create Folium Map ---

# Center the map over Chicago/Cook County area (approx. 41.8, -87.6)
m = folium.Map(location=[41.8781, -87.6298], zoom_start=10, tiles='cartodbpositron')

# Define the color scale based on the dominant race percentage (0-100)
# A high percentage means a high concentration/dominance by one race
max_concentration = 100
# colormap = folium.LinearColormap(
#     ['#ffffb2', '#fecc5c', '#fd8d3c', '#e31a1c', '#800026'],
#     vmin=0, vmax=max_concentration,
#     caption='Dominant Race Concentration (%)'
# )

# colormap.caption = ''
# colormap.add_to(m)

# Make legend text white - updated for record counts
# Create logical record count ranges that group similar values together
max_records = map_data['Total_Records'].max()
min_records = map_data['Total_Records'].min()

# Create logical ranges based on record counts
# Adjust these ranges based on your data distribution
if max_records <= 10:
    # For very low record counts
    ranges = [(1, 1), (2, 2), (3, 4), (5, 7), (8, max_records)]
elif max_records <= 50:
    # For low to medium record counts
    ranges = [(1, 2), (3, 5), (6, 10), (11, 20), (21, max_records)]
elif max_records <= 100:
    # For medium record counts
    ranges = [(1, 3), (4, 8), (9, 15), (16, 30), (31, max_records)]
elif max_records <= 500:
    # For higher record counts
    ranges = [(1, 5), (6, 15), (16, 30), (31, 60), (61, max_records)]
else:
    # For very high record counts
    ranges = [(1, 10), (11, 25), (26, 50), (51, 100), (101, max_records)]

# Create a logical range-based color function
def get_logical_color(records):
    for i, (min_val, max_val) in enumerate(ranges):
        if min_val <= records <= max_val:
            return i + 1  # Return 1-5 based on which range it falls into
    return 1  # Default to lightest if somehow outside all ranges

map_data['Color_Scale'] = map_data['Total_Records'].apply(get_logical_color)

# Create dynamic legend based on logical ranges
legend_html = f"""
<div style="
    position: fixed;
    bottom: 30px;
    left: 30px;
    width: 280px;
    background-color: rgba(30, 30, 30, 0.85);
    border: 1px solid white;
    border-radius: 10px;
    padding: 10px 15px;
    color: white;
    font-size: 14px;
    z-index:9999;
">
<b>Number of Records per ZIP Code</b><br>
<span style='background:#ffffb2; width:20px; height:10px; display:inline-block;'></span> {ranges[0][0]}–{ranges[0][1]}<br>
<span style='background:#fecc5c; width:20px; height:10px; display:inline-block;'></span> {ranges[1][0]}–{ranges[1][1]}<br>
<span style='background:#fd8d3c; width:20px; height:10px; display:inline-block;'></span> {ranges[2][0]}–{ranges[2][1]}<br>
<span style='background:#e31a1c; width:20px; height:10px; display:inline-block;'></span> {ranges[3][0]}–{ranges[3][1]}<br>
<span style='background:#800026; width:20px; height:10px; display:inline-block;'></span> {ranges[4][0]}–{ranges[4][1]}<br>
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# Add custom CSS for better location text readability
location_styling = """
<style>
    /* Improve readability of map labels */
    .leaflet-control-layers label {
        font-size: 14px !important;
        font-weight: bold !important;
        color: #333 !important;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Style for any custom location markers */
    .location-label {
        font-size: 12px !important;
        font-weight: bold !important;
        color: #2c3e50 !important;
        text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.9) !important;
        background-color: rgba(255, 255, 255, 0.8) !important;
        padding: 2px 6px !important;
        border-radius: 3px !important;
        border: 1px solid rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Improve tooltip readability */
    .leaflet-tooltip {
        font-size: 13px !important;
        font-weight: bold !important;
        background-color: rgba(30, 30, 30, 0.9) !important;
        color: white !important;
        border: 2px solid white !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
    }
</style>
"""

m.get_root().html.add_child(folium.Element(location_styling))

# Add the choropleth
folium.Choropleth(
    geo_data=GEOJSON_URL,
    data=map_data,
    columns=[column_zip, 'Color_Scale'],  # Use the quantile-based color scale
    key_on='feature.properties.ZCTA5CE10',
    fill_color='YlOrRd',
    fill_opacity=0.8,
    line_opacity=0.2,
    legend_name='',  # Empty legend name to remove the automatic legend
    highlight=True,
    nan_fill_color='#f0f0f0',  # Light gray for missing data
    nan_fill_opacity=0.3  # Semi-transparent for missing data
).add_to(m)

# Adjust tooltip styling for dark mode
def style_function(feature):
    # Check if this ZIP code has data
    zip_code = feature['properties']['ZCTA5CE10']
    if zip_code in map_data[column_zip].values:
        return {'fillColor': '#ffffff',
                'color': '#000000',
                'fillOpacity': 0.1,
                'weight': 0.1}
    else:
        # Light gray for missing data
        return {'fillColor': '#f0f0f0',
                'color': '#cccccc',
                'fillOpacity': 0.3,
                'weight': 0.1}
highlight_function = lambda x: {'fillColor': '#000000',
                                'color': '#ffffff',  # white outline for better visibility
                                'fillOpacity': 0.50,
                                'weight': 0.3}

N = folium.features.GeoJson(
    GEOJSON_URL,
    name='Race Concentration Data',
    style_function=style_function,
    control=False,
    highlight_function=highlight_function,
    tooltip=folium.features.GeoJsonTooltip(
        fields=['ZCTA5CE10'],
        aliases=['ZIP Code:'],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: rgba(30, 30, 30, 0.9);
            color: white;
            border: 2px solid white;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        """,
        max_width=800,
    )
)
m.add_child(N)


# A function to look up the data for the popup
def popup_info(feature):
    zip_code = feature['properties']['ZCTA5CE10']
    
    if zip_code in map_data[column_zip].values:
        row = map_data[map_data[column_zip] == zip_code].iloc[0]
        dominant_race = row['Dominant_Race']
        percentage = round(row['Dominant_Percentage'], 1)
        total = int(row['Total_Records'])
        
        return f"""
        <b>ZIP Code:</b> {zip_code}<br>
        <b>Total Records:</b> {total}<br>
        <b>Dominant Race:</b> {dominant_race}<br>
        <b>Concentration:</b> {percentage}%
        """
    else:
        return f"<b>ZIP Code:</b> {zip_code}<br>No data available."


# Customizing the GeoJson layer to include popups
for i in N.data['features']:
    i['properties']['popup'] = popup_info(i)

# Add a marker on the map for the popup functionality
folium.GeoJsonPopup(['popup'], parse_html=True).add_to(N)


# --- 4. Save the Map ---
m.save(OUTPUT_MAP_FILE)
print(f"\nInteractive map successfully created!")
print(f"Open '{OUTPUT_MAP_FILE}' in your web browser to view the heatmap.")

