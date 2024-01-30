import pandas as pd
import tkinter as tk
from tkinter.filedialog import askopenfilename

# todo: make file choice with tkinter
# todo: make executable with PyInstaller
# todo: handle 28, 29 (leap years), 30, and 31 dates
# todo: make table and column seletions a user choice, but how?


# Initialize Tkinter
root = tk.Tk()
root.withdraw()  # Hide the main window

# File types options for the dialog
file_types = [("Excel files", "*.xlsx;*.xls"), ("CSV files", "*.csv")]

# Open file dialog and get the file path
file_path = askopenfilename(filetypes=file_types)

# Function to format a date string with leading zeros
def format_date(date_str):
    # Check if the date string contains a range
    if '-' in date_str:
        # Split by hyphen and format each part
        parts = date_str.split('-')
        formatted_parts = [format_single_date(part.strip()) for part in parts]
        return ' - '.join(formatted_parts)
    else:
        return format_single_date(date_str.strip())

# Function to format a single date string with leading zeros
def format_single_date(date_str):
    parts = date_str.split('/')
    formatted_parts = [part.zfill(2) for part in parts]
    return '/'.join(formatted_parts)

# Determine the file extension and load the file accordingly
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
else:
    df = pd.read_excel(file_path)

# Specify the name of the column to format
column_to_format = 'FullDate'

# Create a new column to store the formatted dates
new_column_name = 'FormattedFullDate'

# Check if the specified column exists
if column_to_format not in df.columns:
    print(f"The column '{column_to_format}' does not exist in the file.")
    exit()

# Create a new column with the formatted dates
df[new_column_name] = df[column_to_format].apply(lambda cell: format_date(str(cell)) if pd.notna(cell) else '')

# Save the DataFrame back to the file
if file_path.endswith('.csv'):
    df.to_csv(file_path, index=False)
else:
    df.to_excel(file_path, index=False)