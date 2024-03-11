import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
import time
import re
from datetime import datetime

# Define Progress Bar
def update_progress_bar(progress_bar, value):
    progress_bar['value'] = value
    root.update_idletasks()
    time.sleep(0.5)

# Initialize Tkinter
root = tk.Tk()
root.withdraw()  # Hide the main window

# File types options for the dialog
file_types = [("Excel files", "*.xlsx;*.xls"), ("CSV files", "*.csv")]

# Open file dialog and get the file path
file_path = askopenfilename(filetypes=file_types)

# Progress Window
progress_win = tk.Toplevel(root)
progress_win.title("Processing File")
ttk.Label(progress_win, text="Progress:").pack()
progress_bar = ttk.Progressbar(progress_win, orient='horizontal', length=500, mode='determinate')
progress_bar.pack()
progress_win.update()

# Mapping month names and abbreviations to numbers
month_map = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
    "Jul": "07", "Aug": "08", "Sep": "09", "Sept": "09", "Oct": "10", "Nov": "11", "Dec": "12"
}

# Function to check leap year
def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

# Function to get the last day of a month
def get_last_day_of_month(year, month):
    if month == 2: # February
        return 29 if is_leap_year(year) else 28
    elif month in [4, 6, 9, 11]: # April, June, September, November
        return 30
    else: # January, March, May, July, August, October, December
        return 31


# Function to format a date string with leading zeros
def custom_format_date(date_str):
    # Handling dates with a single '0' day part for range inputs 'MM/0/YYYY - MM/0/YYYY'
    range_zero_day_regex = r'(\d{1,2})/0/(\d{4}) - (\d{1,2})/0/(\d{4})'
    match = re.match(range_zero_day_regex, date_str)
    if match:
        month_start, year_start, month_end, year_end = match.groups()
        # Assuming that the start and end months are the same for this specific transformation
        # Ensure months are formatted as two digits
        month_formatted = f"{int(month_start):02d}"
        # Calculate the last day of the month, considering leap years
        last_day = get_last_day_of_month(int(year_start), int(month_start))
        # Construct the full date range
        start_date = f'{month_formatted}/01/{year_start}'
        end_date = f'{month_formatted}/{last_day}/{year_start}'  # Using start year as range is within the same month and year
        return f'{start_date} - {end_date}'
    
    # Handle 'MM/0/YYYY' format
    single_zero_dd_regex = r'(\d{1,2})/0/(\d{4})'
    match = re.match(single_zero_dd_regex, date_str)
    if match:
        month, year = match.groups()
        last_day = get_last_day_of_month(int(year), int(month))
        start_date = f'{int(month):02d}/01/{year}'
        end_date = f'{int(month):02d}/{last_day}/{year}'
        return f'{start_date} - {end_date}'
    
    # Handling dates in the 'MM//YYYY' format
    blank_dd_regex = r'(\d{1,2})//(\d{4})'
    match = re.match(blank_dd_regex, date_str)
    if match:
        month, year = match.groups()
        last_day = get_last_day_of_month(int(year), int(month))
        start_date = f'{int(month):02d}/01/{year}'
        end_date = f'{int(month):02d}/{last_day}/{year}'
        return f'{start_date} - {end_date}'

    # Split date ranges, accounting for special handling of '??'
    if ' - ' in date_str:
        start_date, end_date = date_str.split(' - ')
        try:
            # Check if either part of the date range contains '??
            if '??' in start_date or '??' in end_date or '00' in start_date or '00' in end_date:

                # Extract month and year for start and end dates
                month_start, _, year_start = start_date.split('/')
                month_end, _, year_end = end_date.split('/')
                
                # Handle '2/??/1999' format to '02/01/1999 - 02/28(or 29)/1999'
                if month_start.isdigit() and year_start.isdigit():
                    last_day_start = get_last_day_of_month(int(year_start), int(month_start))
                    start_date_formatted = f'{int(month_start):02d}/01/{year_start}'
                    end_date_formatted = f'{int(month_end):02d}/{last_day_start}/{year_end}'
                else:
                    return date_str  # Return original if not properly formatted
            else:
                start_date_formatted = datetime.strptime(start_date, '%m/%d/%Y').strftime('%m/%d/%Y')
                end_date_formatted = datetime.strptime(end_date, '%m/%d/%Y').strftime('%m/%d/%Y')
            
            return f'{start_date_formatted} - {end_date_formatted}'
        except ValueError:
            # If there's an error in parsing, return the original string
            return date_str
    else:
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').strftime('%m/%d/%Y')
        except ValueError:
            pass 

    # Handling circa dates
    circa_regex = r'(circa|cir\.?|ca\.?|approx\.?)\s*(\d{4})'
    if re.match(circa_regex, date_str, re.IGNORECASE):
        year = re.findall(circa_regex, date_str, re.IGNORECASE)[0][1]
        return f'circa {year}'

    # Handling timestamp style values
    timestamp_regex = r'\d{4}-\d{2}-\d{2}'
    if re.match(timestamp_regex, date_str):
        date_part = date_str.split(' ')[0]  # Extract just the date part before the space
        return datetime.strptime(date_part, '%Y-%m-%d').strftime('%m/%d/%Y')

    # Handling date ranges and single years
    year_range_regex = r'(\d{4})s?(-\d{4})?'
    if re.match(year_range_regex, date_str):
        if '-' in date_str:
            start_year, end_year = date_str.split('-')
            return f'01/01/{start_year} - 12/31/{end_year}'
        elif 's' in date_str:
            year = date_str.rstrip('s')
            return f'01/01/{year} - 12/31/{int(year)+9}'
        else:
            return f'01/01/{date_str} - 12/31/{date_str}'

    # Handling specific date ranges with question marks
    if '??' in date_str:
        if date_str.count('/') == 2:  # Format: MM/??/YYYY or MM/DD/?? (ignore)
            month, day, year = date_str.split('/')
            if '??' == day:  # Day is unknown, format: MM/??/YYYY
                return f'{month}/01/{year} - {month}/{get_last_day_of_month(int(year), int(month))}/{year}'
            else:  # Format: MM/DD/??, ignore and copy as is
                return date_str
        elif date_str.startswith('??/'):  # Format: ??/YYYY
            year = date_str.split('/')[1]
            return f'01/01/{year} - 12/31/{year}'
        elif '??' in year:  # Year partially unknown, format: MM/DD/19??
            month, day, year_prefix = date_str.split('/')[0], date_str.split('/')[1], date_str.split('/')[2][:2]
            start_year = f'{year_prefix}00'
            end_year = f'{year_prefix}99'
            return f'{month}/{day}/{start_year} - {month}/{day}/{end_year}'

    # Default case: Copy as is
    return date_str

# Determine the file extension and load the file accordingly
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
else:
    df = pd.read_excel(file_path)

# Update progress bar after reading the file
update_progress_bar(progress_bar, 33)

# Specify the name of the column to format
column_to_format = 'FullDate'

# Create a new column to store the formatted dates
new_column_name = 'FormattedFullDate'

# Check if the specified column exists
if column_to_format not in df.columns:
    print(f"The column '{column_to_format}' does not exist in the file.")
    exit()

# Modify the lambda function to use the new custom format function
df[new_column_name] = df[column_to_format].apply(lambda cell: custom_format_date(str(cell)) if pd.notna(cell) else '')

# Update progress bar after processing (date formatting)
update_progress_bar(progress_bar, 66)

# Save the DataFrame back to the file
if file_path.endswith('.csv'):
    df.to_csv(file_path, index=False)
else:
    df.to_excel(file_path, index=False)

# Update progress bar after writing back to the file
update_progress_bar(progress_bar, 100)

# Show completion message
messagebox.showinfo("Completion", "Job completed successfully!")
progress_win.destroy()
