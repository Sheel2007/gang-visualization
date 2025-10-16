import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- Configuration ---
file_path = 'Cook County Regional Gang Intelligence Database.xlsx'
column_colors = 'Subject_Wears_Colors'
column_admits = 'Subject_Admits_Gang'

# --- 1. Data Loading and Setup ---
try:
    # Read the data from the specified Excel file
    df = pd.read_excel(file_path)
    print(f"Data loaded successfully from: {file_path}")
    print(f"Total records: {len(df)}")
except FileNotFoundError:
    print(f"\nERROR: The file '{file_path}' was not found.")
    print("Please ensure the Excel file is in the same directory as this script.")
    
    # Generate sample data for demonstration if file is missing
    data_size = 5000
    df = pd.DataFrame({
        column_colors: np.random.choice(['Y', 'NULL', 'N'], size=data_size, p=[0.4, 0.2, 0.4]),
        column_admits: np.random.choice(['Y', 'NULL', 'N'], size=data_size, p=[0.3, 0.1, 0.6])
    })

except Exception as e:
    print(f"\nAn unexpected error occurred during file reading: {e}")
    exit()

# Check if required columns exist (if using real data)
if column_colors not in df.columns or column_admits not in df.columns:
    print("\nERROR: One or both required columns were not found in the Excel file.")
    print(f"Expected columns: '{column_colors}' and '{column_admits}'")
    print(f"Available columns: {list(df.columns)}")
    exit()


# --- 2. Data Cleaning and Aggregation ---

# Function to standardize the categorical columns to Y (Yes) or N (No/Missing)
def standardize_column(series):
    # Convert all to uppercase string, then replace NULL/NaN with 'N'
    standardized = series.astype(str).str.upper().str.strip()
    standardized = standardized.replace({'NULL': 'N', 'NAN': 'N', 'N/A': 'N'}).fillna('N')
    # Anything not explicitly 'Y' is treated as 'N'
    standardized[standardized != 'Y'] = 'N' 
    return standardized

df['Wears_Colors_Status'] = standardize_column(df[column_colors])
df['Admits_Gang_Status'] = standardize_column(df[column_admits])

# Create the contingency table (2x2 matrix of counts)
# This is the core data for the heatmap
contingency_table = pd.crosstab(
    df['Wears_Colors_Status'],
    df['Admits_Gang_Status'],
    rownames=['Wears Colors?'],
    colnames=['Admits Gang Membership?']
)


# --- 3. Heatmap Visualization ---

plt.figure(figsize=(8, 6))

# Generate the heatmap using Seaborn
sns.heatmap(
    contingency_table, 
    annot=True,          # Show the actual count numbers on the map
    fmt='d',             # Format the annotation as an integer
    cmap='viridis',      # Color map (you can change this, e.g., 'magma', 'YlGnBu')
    linewidths=.5,       # Lines between cells
    linecolor='white',   # Line color
    cbar_kws={'label': 'Number of Subjects'} # Label for the color bar
)

plt.title('Relationship Between Wearing Colors and Gang Admission', fontsize=16, pad=15)
plt.yticks(rotation=0) # Ensure Y-axis labels are horizontal
plt.xticks(rotation=0) # Ensure X-axis labels are horizontal
plt.tight_layout()
plt.show()

