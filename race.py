import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# --- Configuration ---
file_path = 'Cook County Regional Gang Intelligence Database.xlsx'
column_race = 'Subject_Race_ID'
column_admits_gang = 'Subject_Admits_Gang'

# --- 1. Data Loading ---
print(f"Attempting to read data from: {file_path}")

try:
    # Read the data from the Excel file
    # If your data is on a sheet other than the first one, add: sheet_name='Your Sheet Name'
    df = pd.read_excel(file_path)

except FileNotFoundError:
    print(f"\nERROR: The file '{file_path}' was not found.")
    print("Please ensure the Excel file is in the same directory as this script.")
    print("--- Generating sample data for demonstration instead ---")
    
    # Fallback: Generate sample data if the file is not found, so the script still runs.
    np.random.seed(43)
    data_size = 500
    df = pd.DataFrame({
        column_race: np.random.choice(['Black', 'White', 'Hispanic', 'Multiracial', None, 'Black'], size=data_size, p=[0.3, 0.15, 0.4, 0.05, 0.05, 0.05]),
        column_admits_gang: np.random.choice(['Y', 'NULL', None, 'Y'], size=data_size, p=[0.3, 0.3, 0.2, 0.2])
    })
    # Replace the column names for the fallback data
    df.columns = [column_race, column_admits_gang]
    
except Exception as e:
    print(f"\nAn unexpected error occurred during file reading: {e}")
    exit()

# Check if required columns exist
if column_race not in df.columns or column_admits_gang not in df.columns:
    print("\nERROR: One or both required columns were not found in the Excel file.")
    print(f"Expected columns: '{column_race}' and '{column_admits_gang}'")
    print(f"Available columns: {list(df.columns)}")
    exit()

print(f"Data loaded successfully. Total records: {len(df)}")


# --- 2. Data Cleaning and Preparation ---

# Handle missing or 'NULL' race values by setting them to 'Unknown'
race_series = df[column_race].astype(str).str.strip().str.replace('NULL', 'Unknown', case=False)
race_series = race_series.fillna('Unknown').replace('nan', 'Unknown')
df[column_race] = race_series

# Handle missing or 'NULL' gang admission values by setting them to 'N' (No)
admits_gang_series = df[column_admits_gang].astype(str).str.strip().str.replace('NULL', 'N', case=False)
df[column_admits_gang] = admits_gang_series.fillna('N').replace('nan', 'N')


# --- 3. Aggregate Data using Cross-Tabulation (Equivalent to Pivot Table) ---
# Index = Race (X-axis categories)
# Columns = Gang Admits Status (Stacked bar segments)
frequency_table = pd.crosstab(
    df[column_race],
    df[column_admits_gang]
)

# Ensure 'N' and 'Y' columns exist and are in order for consistent color mapping
if 'N' not in frequency_table.columns:
    frequency_table['N'] = 0
if 'Y' not in frequency_table.columns:
    frequency_table['Y'] = 0
frequency_table = frequency_table[['N', 'Y']]

# Calculate the total height for each category (used for labeling logic)
total_heights = frequency_table.sum(axis=1)

print("\n--- Frequency Table (Data for Plotting) ---")
print(frequency_table)
print("\n" + "="*40 + "\n")


# --- 4. Plot the Data as a Stacked Bar Chart ---
fig, ax = plt.subplots(figsize=(12, 7))

# Plot the stacked bar chart
# bars variable holds the artist containers for each series ('N' and 'Y')
bars = frequency_table.plot(
    kind='bar',
    stacked=True,
    ax=ax,
    # Assign colors: Green for 'No Admission' (N) and Red for 'Admission' (Y)
    color=['#4CAF50', '#FF5733'], 
    edgecolor='black'
)

# --- 5. Customization and Labeling (Further Improved Separation) ---

# Thresholds for labeling logic
SMALL_SEGMENT_THRESHOLD = 300      # Segment height below this is placed externally
TINY_TOTAL_BAR_THRESHOLD = 500     # Total bar height below this triggers separated external placement

# Offsets for separated external labels (INCREASED SEPARATION)
Y_N_OFFSET = 30    # Low offset for 'N' label, starting just above the bar
Y_Y_OFFSET = 350   # High offset for 'Y' label, creating a clear vertical gap

# Get X positions of the tick labels for mapping bar positions to total heights
x_positions = [p.get_position()[0] for p in ax.get_xticklabels()]
# Map the X-tick position to the total height of the bar at that position
total_heights_map = dict(zip(x_positions, total_heights.values))


for container_index, container in enumerate(ax.containers):
    # container_index 0 is 'N' (No), 1 is 'Y' (Yes)
    
    # Define color for external label to match the bar color for differentiation
    label_color = '#4CAF50' if container_index == 0 else '#FF5733' # Green or Red

    for bar in container:
        height = bar.get_height()
        
        # Only label non-zero segments
        if height > 0:
            x_pos = bar.get_x() + bar.get_width() / 2  # Center x position
            label_text = int(height)
            
            # Find the closest X-tick position to determine the total bar height
            closest_tick = min(x_positions, key=lambda x: abs(x - x_pos))
            total_height = total_heights_map.get(closest_tick, 0)
            
            
            # --- Logic for Tiny Bars (Ensures N and Y labels are separated vertically) ---
            if total_height > 0 and total_height < TINY_TOTAL_BAR_THRESHOLD:
                
                # Determine the placement based on segment index (N or Y)
                if container_index == 0: # N (No) segment: Place lower
                    y_placement = total_height + Y_N_OFFSET
                else: # Y (Yes) segment: Place higher
                    y_placement = total_height + Y_Y_OFFSET
                    
                ax.text(
                    x_pos, 
                    y_placement, 
                    label_text, 
                    ha='center', 
                    va='bottom', 
                    fontsize=9, 
                    color=label_color, # Use segment color for differentiation
                    fontweight='bold'
                )
            
            # --- Standard Logic (Internal for large, External for small segment in large bar) ---
            elif height < SMALL_SEGMENT_THRESHOLD:
                # Small segment, but part of a large total bar. 
                # Use a neutral black color for better visibility against white background
                ax.text(
                    x_pos, 
                    bar.get_y() + height + Y_N_OFFSET, 
                    label_text, 
                    ha='center', 
                    va='bottom', 
                    fontsize=9, 
                    color='black', 
                    fontweight='bold'
                )
                
            else:
                # Large segment: Place centered inside
                y_pos = bar.get_y() + height / 2  
                ax.text(
                    x_pos, 
                    y_pos, 
                    label_text, 
                    ha='center', 
                    va='center', 
                    fontsize=9, 
                    color='white', 
                    fontweight='bold'
                )


# Recalculate max height to account for the new high Y_Y_OFFSET
max_total_height = total_heights.max()
# Add buffer based on the largest offset (Y_Y_OFFSET)
ax.set_ylim(0, max_total_height + Y_Y_OFFSET + 50) 

# Set Title and Labels
ax.set_title(
    'Gang Admission Status by Subject Race',
    fontsize=18,
    fontweight='bold',
    pad=20
)
ax.set_xlabel('Subject Race ID', fontsize=14)
ax.set_ylabel('Count of Subjects (Frequency)', fontsize=14)

# Customize X-axis ticks
plt.xticks(rotation=45, ha='right', fontsize=12) 

# Customize the Legend
ax.legend(
    title='Admits Gang Status',
    labels=['No (N)', 'Yes (Y)'],
    loc='upper right',
    bbox_to_anchor=(1.2, 1), # Move legend outside the plot area
    fontsize=11
)

# Add grid lines for better readability
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Final layout adjustments
plt.tight_layout(rect=[0, 0, 1, 1]) 
plt.show()

