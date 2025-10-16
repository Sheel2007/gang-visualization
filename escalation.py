import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# --- Configuration ---
file_path = 'Cook County Regional Gang Intelligence Database.xlsx'
column_date = 'Subject_Create_Date'
columns_to_track = ['Subject_Armed', 'Subject_Felon', 'Subject_Probation']

# --- 1. Data Loading ---
print(f"Attempting to read data from: {file_path}")

try:
    # Read the data from the Excel file
    # Ensure the date column is parsed correctly on load
    df = pd.read_excel(file_path, parse_dates=[column_date])

except FileNotFoundError:
    print(f"\nERROR: The file '{file_path}' was not found.")
    print("Please ensure the Excel file is in the same directory as this script.")
    print("--- Generating sample data for demonstration instead ---")
    
    # Fallback: Generate sample data if the file is not found, ensuring a trend is visible
    np.random.seed(45)
    
    # Generate dates from 2010 to 2023
    dates = pd.to_datetime(pd.to_datetime('2010-01-01') + pd.to_timedelta(np.random.randint(0, 365 * 13, 5000), unit='D'))
    
    # Create synthetic data with a slight upward trend over time (simulating escalation)
    def generate_binary_trend(dates, base_prob, annual_increase):
        years = dates.dt.year.astype(int)
        min_year = years.min()
        return np.random.rand(len(dates)) < (base_prob + (years - min_year) * annual_increase)

    df = pd.DataFrame({
        column_date: dates,
        'Subject_Armed': generate_binary_trend(dates, 0.05, 0.005),
        'Subject_Felon': generate_binary_trend(dates, 0.15, 0.01),
        'Subject_Probation': generate_binary_trend(dates, 0.10, 0.008),
    })
    # Convert bools to 'Y' / None for the analysis logic
    for col in columns_to_track:
         df[col] = df[col].apply(lambda x: 'Y' if x else None)
    
except Exception as e:
    print(f"\nAn unexpected error occurred during file reading: {e}")
    exit()

# Check if required columns exist
required_columns = [column_date] + columns_to_track
missing_cols = [col for col in required_columns if col not in df.columns]

if missing_cols:
    print("\nERROR: The following required columns were not found in the Excel file:")
    print(missing_cols)
    print(f"Available columns: {list(df.columns)}")
    exit()

print(f"Data loaded successfully. Total records: {len(df)}")


# --- 2. Data Processing and Aggregation ---

# 2.1 Extract the year
df['Year'] = df[column_date].dt.year

# 2.2 Calculate the total number of records created each year
total_records_per_year = df.groupby('Year').size().rename('Total_Records')

# Initialize a DataFrame to store the final percentage results
trends_df = pd.DataFrame({'Total_Records': total_records_per_year})

# 2.3 Calculate the count and percentage for each 'Escalation Profile' column
for col in columns_to_track:
    # A subject is flagged if the value is NOT NULL (assuming 'Y' or any non-empty value)
    flagged_df = df[df[col].notna() & (df[col].astype(str).str.strip() != '')]
    
    # Count flagged subjects per year
    flagged_count = flagged_df.groupby('Year').size().rename(f'{col}_Count')
    
    # Merge count into the trends DataFrame
    trends_df = trends_df.merge(flagged_count, on='Year', how='left').fillna(0)
    
    # Calculate percentage
    trends_df[f'{col}_Percent'] = (trends_df[f'{col}_Count'] / trends_df['Total_Records']) * 100

print("\n--- Trend Data (Percentage of new records flagged per year) ---")
print(trends_df[[col for col in trends_df.columns if 'Percent' in col]])
print("\n" + "="*60 + "\n")


# --- 3. Plot the Trend Data ---

# Create the figure and axes
fig, ax = plt.subplots(figsize=(14, 8))

# Define the columns to plot
plot_cols = [f'{col}_Percent' for col in columns_to_track]

# Plotting the lines
trends_df[plot_cols].plot(
    kind='line',
    ax=ax,
    linewidth=3,
    marker='o',
    markersize=8
)

# --- 4. Customization ---

# Set Title and Labels
ax.set_title(
    'Escalation Profile: Percentage of New Records Flagged Over Time',
    fontsize=20,
    fontweight='bold',
    pad=20
)
ax.set_xlabel('Year of Record Creation', fontsize=14)
ax.set_ylabel('Percentage of New Records Flagged (%)', fontsize=14)

# Set X-axis ticks to show every year with rotation
ax.set_xticks(trends_df.index)
plt.xticks(rotation=45, ha='right', fontsize=12) 

# Ensure Y-axis starts at 0
ax.set_ylim(bottom=0)

# Customize the Legend
legend_labels = [col.replace('_', ' ').replace('Subject ', '') for col in columns_to_track]
ax.legend(
    legend_labels,
    title='Flag Type',
    loc='upper left',
    fontsize=12,
    shadow=True
)

# Add grid lines for better readability
ax.grid(axis='both', linestyle='--', alpha=0.7)

# Add a text label to highlight the analysis focus
plt.figtext(
    0.5, 0.01, 
    'Analysis shows the rate at which newly entered subjects are flagged with severe profiles.',
    ha='center', fontsize=10, color='gray'
)

# Final layout adjustments
plt.tight_layout(rect=[0, 0.05, 1, 1]) 
plt.show()

