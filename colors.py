import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# --- Configuration ---
file_path = 'Cook County Regional Gang Intelligence Database.xlsx'
column_wears_colors = 'Subject_Wears_Colors'
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
    np.random.seed(42)
    data_size = 500
    df = pd.DataFrame({
        column_wears_colors: np.random.choice(['Y', None, 'Y', 'Y'], size=data_size, p=[0.4, 0.2, 0.3, 0.1]),
        column_admits_gang: np.random.choice(['Y', 'NULL', None], size=data_size, p=[0.2, 0.5, 0.3])
    })
    # Replace the column names for the fallback data
    df.columns = [column_wears_colors, column_admits_gang]
    
except Exception as e:
    print(f"\nAn unexpected error occurred during file reading: {e}")
    exit()

# Check if required columns exist in the DataFrame
if column_wears_colors not in df.columns or column_admits_gang not in df.columns:
    print("\nERROR: One or both required columns were not found in the Excel file.")
    print(f"Expected columns: '{column_wears_colors}' and '{column_admits_gang}'")
    print(f"Available columns: {list(df.columns)}")
    exit()

print(f"Data loaded successfully. Total records: {len(df)}")
print("\n" + "="*40 + "\n")


# --- 2. Data Cleaning and Preparation ---

# Convert explicit 'NULL' strings and pandas NaNs (from empty cells) to 'N' for 'No'
# This ensures all non-'Y' values are treated as a single 'No' category for graphing.
df[column_wears_colors] = df[column_wears_colors].fillna('N').replace('NULL', 'N')
df[column_admits_gang] = df[column_admits_gang].fillna('N').replace('NULL', 'N')

# Optional: Only keep 'Y' and 'N' for graphing
df = df[df[column_wears_colors].isin(['Y', 'N']) & df[column_admits_gang].isin(['Y', 'N'])]


# --- 3. Aggregate Data using Cross-Tabulation (Equivalent to Pivot Table) ---
# Create a frequency table showing the count of each combination.
frequency_table = pd.crosstab(
    df[column_wears_colors],
    df[column_admits_gang]
)

# Sort the index/columns for consistent plotting order: 'N' then 'Y'
frequency_table = frequency_table.reindex(index=['N', 'Y'], fill_value=0)
if 'N' in frequency_table.columns and 'Y' in frequency_table.columns:
    frequency_table = frequency_table[['N', 'Y']]

print("--- Frequency Table (Data for Plotting) ---")
print(frequency_table)
print("\n" + "="*40 + "\n")


# --- 4. Plot the Data as a Stacked Bar Chart ---
fig, ax = plt.subplots(figsize=(10, 7))

# Plot the stacked bar chart directly from the frequency table
frequency_table.plot(
    kind='bar',
    stacked=True,
    ax=ax,
    color=['#3366CC', '#CC0000'], # Blue for N (No Admit), Red for Y (Admit)
    edgecolor='black'
)

# --- 5. Customization and Labeling ---

# Set Title and Labels
ax.set_title(
    'Correlation: Colors Worn vs. Gang Admission Status',
    fontsize=16,
    fontweight='bold',
    pad=20
)
ax.set_xlabel('Subject Wears Colors', fontsize=13)
ax.set_ylabel('Count of Subjects (Frequency)', fontsize=13)

# Customize X-axis ticks (Wears Colors)
ax.set_xticklabels(['No (N)', 'Yes (Y)'], rotation=0, ha='center', fontsize=12)

# Customize the Legend
ax.legend(
    title='Subject Admits Gang Status',
    labels=['No (N)', 'Yes (Y)'],
    loc='upper right',
    bbox_to_anchor=(1.35, 1) # Move legend outside the plot area
)

# Add grid lines for better readability
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Add value labels to the bars
for container in ax.containers:
    # Add labels showing the exact count on each segment
    ax.bar_label(container, label_type='center', fontsize=10, color='white', fontweight='bold')

# Final layout adjustments
plt.tight_layout(rect=[0, 0, 0.9, 1]) # Adjust for external legend
plt.show()

