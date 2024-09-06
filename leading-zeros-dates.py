import  pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
import time
import re
from datetime import datetime, timedelta

# Initialize column_to_format
column_to_format = None

# Initialize Tkinter
root = tk.Tk()
root.withdraw()  # Hide the main window

# Define Progress Bar
def update_progress_bar(progress_bar, value):
    progress_bar['value'] = value
    root.update_idletasks()
    time.sleep(0.5)


# Function to select the file
def select_file():
    file_types = [("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
    try:
        file_path = askopenfilename(filetypes=file_types)
        if not file_path:
            messagebox.showerror("Error", "No file selected. Exiting.")
            root.destroy()
            exit()
        return file_path
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while selecting a file: {str(e)}")
        root.destroy()
        exit()

# Select the file
file_path = select_file()

# Determine the file extension and load the file accordingly
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
else:
    df = pd.read_excel(file_path)


# Progress Window
progress_win = tk.Toplevel(root)
progress_win.title("Processing File")
ttk.Label(progress_win, text="Progress:").pack()
progress_bar = ttk.Progressbar(progress_win, orient='horizontal', length=500, mode='determinate')
progress_bar.pack()
progress_win.update()

# Mapping month names and abbreviations to numbers
month_map = {
    "Jan": "01", "January": "01",
    "Feb": "02", "February": "02",
    "Mar": "03", "March": "03",
    "Apr": "04", "April": "04",
    "May": "05",
    "Jun": "06", "June": "06",
    "Jul": "07", "July": "07",
    "Aug": "08", "August": "08",
    "Sep": "09", "Sept": "09", "September": "09",
    "Oct": "10", "October": "10",
    "Nov": "11", "November": "11",
    "Dec": "12", "December": "12"
}


# Function to check leap year
def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


# Function to get the last day of a month
def get_last_day_of_month(year, month):
    if month == 2:  # February
        return 29 if is_leap_year(year) else 28
    elif month in [4, 6, 9, 11]:  # April, June, September, November
        return 30
    else:  # January, March, May, July, August, October, December
        return 31


# Function to prompt the user to select a column from a dropdown list
def select_column():
    global column_to_format
    column_selection_win = tk.Toplevel(root)
    column_selection_win.title("Select Column to Format")
    column_selection_win.geometry("400x250")

    selected_column = tk.StringVar(column_selection_win)
    selected_column.set(df.columns[0])  # Set default value to the first column

    tk.Label(column_selection_win, text="Select the column to format:").pack()
    tk.OptionMenu(column_selection_win, selected_column, *df.columns).pack()

    def on_confirm():
        global column_to_format
        column_to_format = selected_column.get()
        column_selection_win.destroy()

    def on_cancel():
        column_selection_win.destroy()
        root.destroy()

    tk.Button(column_selection_win, text="Confirm", command=on_confirm).pack()
    tk.Button(column_selection_win, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=20, pady=20)

    column_selection_win.grab_set()
    root.wait_window(column_selection_win)


# Main function to handle date formatting
def custom_format_date(date_str):
    try:

        # First, normalize the date string to ensure leading zeros for month/day
        def add_leading_zeros(date):
            # Regular expression to match a date in the format M/D/YYYY or M/DD/YYYY or MM/D/YYYY
            date = re.sub(r'\b(\d{1})/(\d{1,2})/(\d{4})', r'0\1/\2/\3', date)  # Add leading zero to month
            date = re.sub(r'(\d{2})/(\d{1})/(\d{4})', r'\1/0\2/\3', date)      # Add leading zero to day
            return date

        # Apply the function to add leading zeros where necessary
        date_str = add_leading_zeros(date_str)

        # Check if the input is already a valid date range in MM/DD/YYYY - MM/DD/YYYY format
        valid_date_range_pattern = r'^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$'
        if re.match(valid_date_range_pattern, date_str):
            # If it's a valid date range, return it as-is
            return (date_str, '')

        # Handle exact list of years, excluding single years and years with non-year characters
        year_list_pattern = r'^\d{4}([,;\s-]+\d{4}){1,}$'
        match = re.fullmatch(year_list_pattern, date_str)
        if match:
            years = sorted({int(year) for year in re.findall(r'\d{4}', date_str)})
            if len(years) > 1:
                start_year = years[0]
                end_year = years[-1]
                return (f'01/01/{start_year} - 12/31/{end_year}', 'Y')

        # Handle date range in the format "Month Day, Year – Month Day, Year" with both en dash and hyphen-minus
        full_date_range_pattern = r'([A-Za-z]+)\s(\d{1,2}),?\s(\d{4})\s[–-]\s([A-Za-z]+)\s(\d{1,2}),?\s(\d{4})'
        match = re.match(full_date_range_pattern, date_str)
        if match:
            start_month, start_day, start_year, end_month, end_day, end_year = match.groups()
            start_date = f'{month_map[start_month[:3].capitalize()]}/{start_day.zfill(2)}/{start_year}'
            end_date = f'{month_map[end_month[:3].capitalize()]}/{end_day.zfill(2)}/{end_year}'
            return (f'{start_date} - {end_date}', '')

        # Handle abbreviated month date range in the format "Month Day, Year - Month Day, Year"
        abbreviated_month_date_range_pattern = r'([A-Za-z]+)\s(\d{1,2}),\s(\d{4})\s-\s([A-Za-z]+)\s(\d{1,2}),\s(\d{4})'
        match = re.match(abbreviated_month_date_range_pattern, date_str)
        if match:
            start_month, start_day, start_year, end_month, end_day, end_year = match.groups()
            start_date = f'{month_map[start_month[:3]]}/{start_day.zfill(2)}/{start_year}'
            end_date = f'{month_map[end_month[:3]]}/{end_day.zfill(2)}/{end_year}'
            return (f'{start_date} - {end_date}', '')

        # Match full and abbreviated month names, optionally with '.' and day/year formats
        date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})'
        match = re.match(date_pattern, date_str, re.IGNORECASE)
        if match:
            month, day, year = match.groups()
            return (f'{month_map[month.capitalize()[:3]]}/{day.zfill(2)}/{year}', '')

        # Check for 'vol' or 'volume' patterns with a year and optional numbers following
        vol_pattern = r'(\d{4})\s+(vol|volume)\b.*'
        match = re.match(vol_pattern, date_str, re.IGNORECASE)
        if match:
            year = match.group(1)
            return (f'01/01/{year} - 12/31/{year}', 'Y')

        # N.D., n.d., nd, No Date, not dated, U.D., u.d., ud
        if re.search(r'\b(N\.?\s*D\.?|n\.?\s*d\.?|U\.?\s*D\.?|u\.?\s*d\.?|No Date|not dated)\b', date_str, re.IGNORECASE):
            return ('undated', '')

        # Handle excel 5-digit serial date ranges or incomplete ranges
        excel_serial_range_pattern = r'(\d{5})? ?- ?(\d{5})?'
        match = re.match(excel_serial_range_pattern, date_str)
        
        if match:
            start_serial, end_serial = match.groups()
            excel_start_date = datetime(1899, 12, 31)

            def convert_serial(serial):
                if not serial:
                    return None
                serial_int = int(serial)
                if serial_int > 59:
                    serial_int += 1  # Handle Excel's leap year bug for dates after 2/28/1900
                serial_converted = excel_start_date + timedelta(days=serial_int - 1)
                return serial_converted.strftime('%m/%d/%Y')

            # Convert start and end serial numbers to dates
            start_date = convert_serial(start_serial)
            end_date = convert_serial(end_serial)

            # Handle various cases based on what was present in the input
            if start_date and end_date:
                return (f'{start_date} - {end_date}', '')
            elif start_date:
                return (f'after {start_date}', 'Y')  # Incomplete end
            elif end_date:
                return (f'before {end_date}', 'Y')  # Incomplete start

        # Check for dates in 'YYYY-MM-DD' or 'YYYY/MM/DD' formats, with support for single-digit months and days
        iso_date_pattern = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        match = re.match(iso_date_pattern, date_str)
        if match:
            year, month, day = match.groups()
            # Pad the month and day with zeros if needed
            return (f'{int(month):02d}/{int(day):02d}/{year}', '')

        # Check for 'post', 'pre', or 'ante' patterns and return immediately if matched
        before_after_patterns = [
            (r'(?i)\bpost[- ]*(\d{4})\b', 'after {year}'),
            (r'(?i)\bpre[- ]*(\d{4})\b', 'before {year}'),
            (r'(?i)\bante\.?[- ]*(\d{4})\b', 'before {year}'),
        ]

        for pattern, format_str in before_after_patterns:
            match = re.search(pattern, date_str)
            if match:
                year = match.group(1)  # Capture the year
                return (format_str.format(year=year), 'Y')

        # Handling timestamp style values
        timestamp_regex = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
        if re.match(timestamp_regex, date_str):
            date_part = date_str.split(' ')[0]  # Extract just the date part before the space
            return (datetime.strptime(date_part, '%Y-%m-%d').strftime('%m/%d/%Y'), '')

        # Handle full year range with two different years (e.g., 1971-1972 or 1971 - 1972)
        full_year_range_pattern = r'(\d{4})\s*-\s*(\d{4})'
        match = re.match(full_year_range_pattern, date_str)
        if match:
            start_year, end_year = match.groups()
            return (f'01/01/{start_year} - 12/31/{end_year}', '')

        # Handle year-month to year-month (e.g., 1992/01 - 1992/03)
        year_month_to_year_month_pattern = r'(\d{4})/(\d{2}) - (\d{4})/(\d{2})'
        match = re.match(year_month_to_year_month_pattern, date_str)
        if match:
            start_year, start_month, end_year, end_month = match.groups()
            last_day_of_end_month = get_last_day_of_month(int(end_year), int(end_month))
            return (f'{start_month}/01/{start_year} - {end_month}/{last_day_of_end_month}/{end_year}', '')

        # Handle two-digit year range within the same century (e.g., 1974-75)
        two_digit_year_range_pattern = r'(\d{4})-(\d{2})'
        match = re.match(two_digit_year_range_pattern, date_str)
        if match:
            start_year_full, end_year_two_digit = match.groups()
            end_year_full = int(start_year_full[:2] + end_year_two_digit)
            if int(end_year_two_digit) < int(start_year_full[2:]):
                end_year_full += 100  # Adjust century
            return (f'01/01/{start_year_full} - 12/31/{end_year_full}', '')

        # Handle question marked date ranges
        question_mark_date_ranges = [
        (r'^\?{1,2} - (\d{1,2})/(\d{1,2})/(\d{4})$', lambda month, day, year: f'before {int(month):02d}/{int(day):02d}/{year}'),
        (r'^\?{1,2} - (\d{4})$', lambda year: f'before {year}'),
        (r'(\d{1,2})/(\d{1,2})/(\d{4}) - \?{1,2}$', lambda month, day, year: f'after {int(month):02d}/{int(day):02d}/{year}'),
        ]

        for pattern, action in question_mark_date_ranges:
            match = re.match(pattern, date_str)
            if match:
                return (action(*match.groups()), 'Y')

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
            # Using start year as range is within the same month and year
            end_date = f'{month_formatted}/{last_day}/{year_start}'
            return (f'{start_date} - {end_date}', '')

        # Handle 'MM/0/YYYY' format
        single_zero_dd_regex = r'(\d{1,2})/0/(\d{4})'
        match = re.match(single_zero_dd_regex, date_str)
        if match:
            month, year = match.groups()
            last_day = get_last_day_of_month(int(year), int(month))
            start_date = f'{int(month):02d}/01/{year}'
            end_date = f'{int(month):02d}/{last_day}/{year}'
            return (f'{start_date} - {end_date}', '')

        # Handling dates in the 'MM//YYYY' format
        blank_dd_regex = r'(\d{1,2})//(\d{4})'
        match = re.match(blank_dd_regex, date_str)
        if match:
            month, year = match.groups()
            last_day = get_last_day_of_month(int(year), int(month))
            start_date = f'{int(month):02d}/01/{year}'
            end_date = f'{int(month):02d}/{last_day}/{year}'
            return (f'{start_date} - {end_date}', '')

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

                return (f'{start_date_formatted} - {end_date_formatted}', '')
            except ValueError:
                # If there's an error in parsing, return the original string
                return (date_str, '')
        else:
            try:
                return (datetime.strptime(date_str, '%m/%d/%Y').strftime('%m/%d/%Y'), '')
            except ValueError:
                pass

        # Handling circa dates
        circa_regex = r'(circa|cir\.?|ca\.?|approx\.?|c\.?)\s*(\d{4})'
        if re.match(circa_regex, date_str, re.IGNORECASE):
            year = re.findall(circa_regex, date_str, re.IGNORECASE)[0][1]
            return (f'circa {year}', 'Y')

        # Handling date ranges and single years
        year_range_regex = r'(\d{4})s?(-\d{4})?'
        if re.match(year_range_regex, date_str):
            if '-' in date_str:
                start_year, end_year = date_str.split('-')
                return (f'01/01/{start_year} - 12/31/{end_year}', '')
            elif 's' in date_str:
                year = date_str.rstrip('s')
                return (f'01/01/{year} - 12/31/{int(year)+9}', '')
            else:
                return (f'01/01/{date_str} - 12/31/{date_str}', '')

        # Handling specific date ranges with question marks
        if '??' in date_str:
            if date_str.count('/') == 2:  # Format: MM/??/YYYY or MM/DD/?? (ignore)
                month, day, year = date_str.split('/')
                if '??' == day:  # Day is unknown, format: MM/??/YYYY
                    return (f'{month}/01/{year} - {month}/{get_last_day_of_month(int(year), int(month))}/{year}', '')
                else:  # Format: MM/DD/??, ignore and copy as is
                    return (date_str, '')
            elif date_str.startswith('??/'):  # Format: ??/YYYY
                year = date_str.split('/')[1]
                return (f'01/01/{year} - 12/31/{year}', '')


        # Handling for full month names and years, converting to range
        month_range_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})'
        match = re.match(month_range_pattern, date_str, re.IGNORECASE)
        if match:
            month, year = match.groups()
            last_day = get_last_day_of_month(int(year), int(month_map[month.capitalize()[:3]]))
            return (f'{month_map[month.capitalize()[:3]]}/01/{year} - {month_map[month.capitalize()[:3]]}/{last_day}/{year}', '')

        # Handling for year-only formats with month abbreviations (e.g., Nov-86)
        abbreviated_year_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[-.]\s*(\d{2})'
        match = re.match(abbreviated_year_pattern, date_str, re.IGNORECASE)
        if match:
            month, year = match.groups()
            # Assuming any year '86' is 1986 (adapt as necessary)
            year = f'19{year}' if int(year) < 50 else f'20{year}'
            last_day = get_last_day_of_month(int(year), int(month_map[month.capitalize()[:3]]))
            return (f'{month_map[month.capitalize()[:3]]}/01/{year} - {month_map[month.capitalize()[:3]]}/{last_day}/{year}', '')

        # Handling Named Months with Ranges
        named_month_range_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s+(?:-|)\s*(?:\1\s+)?(\d{1,2})\s+(\d{4})'
        match = re.match(named_month_range_pattern, date_str, re.IGNORECASE)
        if match:
            start_month_name, start_day, end_day, year = match.groups()

            # Normalize the month name to its numeric representation using the month_map
            month_number = month_map[start_month_name.capitalize()]

            # Format the start and end dates into the desired MM/DD/YYYY format
            formatted_start_date = f'{month_number}/{start_day.zfill(2)}/{year}'
            formatted_end_date = f'{month_number}/{end_day.zfill(2)}/{year}'

            return (f'{formatted_start_date} - {formatted_end_date}', '')

        # Default case: Copy as is
        return (date_str, 'Y')

    except Exception as e:
        return (date_str, 'Y')


def convert_strange_named_ranges(date_str):
    # Enhanced regex to handle both full and abbreviated month names, and optional end month and year
    matches = re.search(r'(\b[A-Za-z]+) (\d{1,2})( \d{4})? - (\b[A-Za-z]*\b)? ?(\d{1,2})( \d{4})?', date_str)
    if not matches:
        return date_str  # Return the original string if regex does not match

    start_month, start_day, start_year_optional, end_month_optional, end_day, end_year_optional = matches.groups()

    start_year = start_year_optional if start_year_optional else end_year_optional
    end_month = end_month_optional if end_month_optional else start_month

    start_date_str = f"{start_month} {start_day} {start_year}"
    end_date_str = f"{end_month} {end_day} {end_year_optional}"

    for date_format in ("%B %d %Y", "%b %d %Y"):
        try:
            start_date = datetime.strptime(start_date_str, date_format)
            break
        except ValueError:
            continue
    else:
        return date_str  # Return the original string if start date cannot be parsed

    for date_format in ("%B %d %Y", "%b %d %Y"):
        try:
            end_date = datetime.strptime(end_date_str, date_format)
            break
        except ValueError:
            continue
    else:
        return date_str  # Return the original string if end date cannot be parsed

    converted_start_date = start_date.strftime("%m/%d/%Y")
    converted_end_date = end_date.strftime("%m/%d/%Y")

    return f"{converted_start_date} - {converted_end_date}"

# Update progress bar after reading the file
update_progress_bar(progress_bar, 33)

# Prompt the user to select the column to format
select_column()

# Check if the specified column exists
if column_to_format not in df.columns:
    print(f"The column '{column_to_format}' does not exist in the file.")
    exit()

# Create a new column to store the formatted dates
new_column_name = f'Formatted{column_to_format}'

# Apply custom_format_date to create the new column and Check Me column
df['temp'] = df[column_to_format].apply(lambda cell: custom_format_date(str(cell)) if pd.notna(cell) else ('undated', ''))
df[new_column_name], df['Check Me'] = zip(*df['temp'])
df.drop(columns=['temp'], inplace=True)  # Clean up the temporary column

# Apply convert_strange_named_ranges to the new_column_name column
df[new_column_name] = df[new_column_name].apply(convert_strange_named_ranges)

# Update progress bar after processing (date formatting)
update_progress_bar(progress_bar, 66)


def ensure_chronological_order(date_str):
    # Regular expression to match date ranges in the format MM/DD/YYYY - MM/DD/YYYY
    fix_chrono_range_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4}) - (\d{1,2})/(\d{1,2})/(\d{4})'
    match = re.match(fix_chrono_range_pattern, date_str)
    if match:
        # Extract dates and ensure month and day are two digits
        start_month, start_day, start_year, end_month, end_day, end_year = match.groups()

        # Form date strings
        start_date_str = f'{int(start_month):02d}/{int(start_day):02d}/{start_year}'
        end_date_str = f'{int(end_month):02d}/{int(end_day):02d}/{end_year}'

        try:
            # Parse date strings to datetime objects for comparison
            start_date = datetime.strptime(start_date_str, '%m/%d/%Y')
            end_date = datetime.strptime(end_date_str, '%m/%d/%Y')

            # Swap dates if the start date is later than the end date
            if start_date > end_date:
                start_date, end_date = end_date, start_date

            # Format dates back into strings without altering the day
            formatted_start_date = start_date.strftime('%m/%d/%Y')
            formatted_end_date = end_date.strftime('%m/%d/%Y')

            return f'{formatted_start_date} - {formatted_end_date}'

        except ValueError:
            # Skip over dates that can't be parsed and return original string
            return date_str

    # Return the original string if no match or if parsing failed
    return date_str


def is_valid_date_format(date_str):
    valid_patterns = [
        r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY - MM/DD/YYYY
        r'^undated$'  # undated
    ]
    return any(re.match(pattern, date_str) for pattern in valid_patterns)

# Apply the function to the DataFrame
df[new_column_name] = df[new_column_name].apply(ensure_chronological_order)

# Analyze the new_column_name column and update the Check Me column
df['Check Me'] = df.apply(lambda row: 'Y' if not is_valid_date_format(row[new_column_name]) and row['Check Me'] != 'Y' else row['Check Me'], axis=1)

# Add a "Y" to the Check Me column if a semi-colon exists in the FullDate column, ensuring no duplicate "Y"
df['Check Me'] = df.apply(lambda row: 'Y' if isinstance(row[column_to_format], str) and ';' in row[column_to_format] and row['Check Me'] != 'Y' else row['Check Me'], axis=1)

# Ensure RG column is formatted with at least 4 digits
if 'RG' in df.columns:
    df['RG'] = df['RG'].apply(lambda x: f'{int(x):04d}' if pd.notna(x) and x != '' else x)

# Ensure SubGr, Series, and SubSeries columns are formatted with at least 3 digits
for col in ['SubGr', 'SG', 'SubGroup', 'Series', 'SubSeries Number']:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: f'{int(x):03d}' if pd.notna(x) and x != '' else x)

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
