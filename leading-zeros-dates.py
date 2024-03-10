import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
import time
import re
from datetime import datetime

# Todos:

# todo: if FullDate has circa, cir, cir., ca, ca., approx, approx. followed by a year, that should copy over to formatted date with circa and the year. E.g.: circa 1765 = circa 1765; cir 1700 = circa 1700; ca 1890 = circa 1890; approx 1999 = circa 1999 

# todo: timestamp style values in FullDate should be converted to MM/DD/YYYY. E.g.: 1908-12-15  12:00:00 AM = 12/15/1908

# todo: dates and date ranges in FullDate should be converted like so: 1900 = 01/01/1900 - 12/31/1999; 1900s = 01/01/1900 - 12/31/1999; 1901-1902 - 01/01/1901 - 12/31/1902; some dates may have question marks and they should be converted like so: 10/??/1901 = 10/01/1901 - 10/31/1901; ??/1900 = 01/01/1900 - 12/31/1900; 10/01/19?? = 10/01/1901 - 10/01/1999

# todo: script should complete date ranges with the correct days of the month. e.g.: 01/01/2000 - 01/31/2000; 02/01/1999 - 02/28/1999; 03/01/2001 - 03/31/2001; 04/01/2002 - 04/30/2002
    
# todo: script should complete date ranges with the correct days for Feburary in leap years. e.g.: 02/01/1999 - 02/28/1999; 02/01/2000 - 02/29/2000; 02/01/2001 - 02/28/2001; 02/01/2024 - 02/29/2024

# todo: anything not matching the above todos should be copied to FormattedDate as is, including blanks


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
    # Check if the date_str represents a range
    if ' - ' in date_str:  # Ensure to check for ' - ' (with spaces as used in split)
        # Split the range into start and end dates only if ' - ' is present
        start_date, end_date = date_str.split(' - ')
        # Process each date in the range individually to ensure MM/DD/YYYY format
        try:
            start_date_formatted = datetime.strptime(start_date, '%m/%d/%Y').strftime('%m/%d/%Y')
            end_date_formatted = datetime.strptime(end_date, '%m/%d/%Y').strftime('%m/%d/%Y')
            # Combine back into a range string
            return f'{start_date_formatted} - {end_date_formatted}'
        except ValueError:
            # If there's an error in parsing, return the original string
            return date_str
    else:
        # For single dates or strings without ' - ', try to format with leading zeros
        try:
            # This will correctly format single dates
            return datetime.strptime(date_str, '%m/%d/%Y').strftime('%m/%d/%Y')
        except ValueError:
            # If parsing the single date fails, it might not be a simple date.
            # No change is made, and further handling could be applied below if needed.
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
