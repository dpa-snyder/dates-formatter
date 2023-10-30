import pandas as pd

# Replace 'your_excel_file.xlsx' with the path to your Excel file
file_path = '1800_Revolutionary_War_Records_for_script.xlsx'

# Load the Excel file into a pandas DataFrame
df = pd.read_excel(file_path)

# Specify the name of the column to format
column_to_format = 'FullDate'

# Create a new column to store the formatted dates
new_column_name = 'FormattedDate'

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

# Create a new column with the formatted dates
df[new_column_name] = df[column_to_format].apply(lambda cell: format_date(str(cell)) if pd.notna(cell) else '')

# Replace the existing Excel file with the updated DataFrame
df.to_excel(file_path, index=False)
