import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
from datetime import datetime, timedelta
import re
import time

# Initialize Tkinter
root = tk.Tk()
root.withdraw()

# Function to select a file
def select_file():
    file_path = askopenfilename()
    if not file_path:
        messagebox.showerror("Error", "No file selected. Exiting.")
        root.destroy()
        exit()
    return file_path

# Function to select a column
def select_column(df):
    column_selection_win = tk.Toplevel(root)
    column_selection_win.title("Select Column to Format")
    column_selection_win.geometry("350x350")  # Set window size to 350x350 pixels
    selected_column = tk.StringVar(column_selection_win)
    selected_column.set(df.columns[0])

    tk.Label(column_selection_win, text="Select the column to format:").pack()
    tk.OptionMenu(column_selection_win, selected_column, *df.columns).pack()

    def on_confirm():
        column_selection_win.destroy()

    def on_cancel():
        column_selection_win.destroy()
        root.destroy()
        exit()

    tk.Button(column_selection_win, text="Confirm", command=on_confirm).pack()
    tk.Button(column_selection_win, text="Cancel", command=on_cancel).pack()
    
    column_selection_win.grab_set()
    root.wait_window(column_selection_win)
    return selected_column.get()

# Helper function to check if a year is a leap year
def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

# Helper function to get the last day of a month
def get_last_day_of_month(year, month):
    if month == 2:
        return 29 if is_leap_year(year) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    return 31

def is_excel_serial_text(value):
    return bool(re.fullmatch(r'\d{5}', str(value)))


def excel_serial_to_date(serial_text):
    serial = int(serial_text)
    base = datetime(1899, 12, 30) if serial >= 60 else datetime(1899, 12, 31)
    return (base + timedelta(days=serial)).strftime('%m/%d/%Y')


def _pad_alnum(val, width):
    """Pad numeric portion of an ID to `width` chars; preserves leading letter (e.g. W22)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return val
    s = str(val).strip()
    if s == '':
        return s
    m = re.match(r'^([A-Za-z]?)(\d+)$', s)
    if not m:
        return s
    prefix, digits = m.groups()
    pad = max(0, width - len(prefix))
    return f'{prefix}{digits.zfill(pad)}'


def ensure_chronological_order(date_str):
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4}) - (\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if not m:
        return date_str
    sm, sd, sy, em, ed, ey = m.groups()
    try:
        s = datetime.strptime(f'{int(sm):02d}/{int(sd):02d}/{sy}', '%m/%d/%Y')
        e = datetime.strptime(f'{int(em):02d}/{int(ed):02d}/{ey}', '%m/%d/%Y')
        if s > e:
            s, e = e, s
        return f'{s.strftime("%m/%d/%Y")} - {e.strftime("%m/%d/%Y")}'
    except ValueError:
        return date_str


month_map = {
    "Jan": "01", "January": "01", "Feb": "02", "February": "02",
    "Mar": "03", "March": "03", "Apr": "04", "April": "04", "May": "05",
    "Jun": "06", "June": "06", "Jul": "07", "July": "07",
    "Aug": "08", "August": "08", "Sep": "09", "Sept": "09", "September": "09",
    "Oct": "10", "October": "10", "Nov": "11", "November": "11",
    "Dec": "12", "December": "12",
}


# Function to convert date patterns
def convert_date_pattern(date_str):
    try:
        # Skip if the date is already in the desired format
        if re.match(r'\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}', date_str):
            return date_str

        date_str = re.sub(r'\s*\(.*?\)', '', date_str).strip()
        if is_excel_serial_text(date_str):
            return excel_serial_to_date(date_str)
        m = re.fullmatch(r'(\d{5})?\s*-\s*(\d{5})?', date_str)
        if m:
            start_serial, end_serial = m.groups()
            start_date = excel_serial_to_date(start_serial) if start_serial else ''
            end_date = excel_serial_to_date(end_serial) if end_serial else ''
            if start_date and end_date:
                return f'{start_date} - {end_date}'
            if start_date:
                return start_date
            if end_date:
                return end_date
        if re.search(r'\b(N\.?\s*D\.?|n\.?\s*d\.?|U\.?\s*D\.?|u\.?\s*d\.?|No Date|not dated|undated)\b',
                     date_str, re.IGNORECASE):
            return 'undated'
        if re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$', date_str):
            return datetime.strptime(date_str.split()[0], '%Y-%m-%d').strftime('%m/%d/%Y')

        if re.match(r'\d{4}-\d{2}-\d{2}$', date_str):
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%m/%d/%Y')

        if re.match(r'\d{4}-\d{4}$', date_str):
            start_year, end_year = map(int, date_str.split('-'))
            return f"01/01/{start_year} - 12/31/{end_year}"

        if re.match(r'\d{4}/\d{4}-\d{2}$', date_str):
            start_year, end_part = date_str.split('/')
            end_year, end_month = map(int, end_part.split('-'))
            end_day = get_last_day_of_month(end_year, end_month)
            return f"01/01/{start_year} - {end_month:02d}/{end_day}/{end_year}"

        if re.match(r'\d{4}-\d{2}/\d{4}$', date_str):
            start_part, end_year = date_str.split('/')
            start_year, start_month = map(int, start_part.split('-'))
            end_date = f"12/31/{end_year}"
            start_date = f"{start_month:02d}/01/{start_year}"
            return f"{start_date} - {end_date}"

        if re.match(r'\d{4}-\d{2}/\d{4}-\d{2}$', date_str):
            start_part, end_part = date_str.split('/')
            start_year, start_month = map(int, start_part.split('-'))
            end_year, end_month = map(int, end_part.split('-'))
            start_date = f"{start_month:02d}/01/{start_year}"
            end_date = f"{end_month:02d}/{get_last_day_of_month(end_year, end_month)}/{end_year}"
            return f"{start_date} - {end_date}"

        if re.match(r'\d{4}/\d{4}(?:/\d{4})*', date_str):
            years = list(map(int, date_str.split('/')))
            return f"01/01/{years[0]} - 12/31/{years[-1]}"

        if re.match(r'\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$', date_str):
            start_date, end_date = date_str.split('/')
            start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%m/%d/%Y')
            end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
            return f"{start_date_formatted} - {end_date_formatted}"

        if re.match(r'\d{4}-\d{2}$', date_str):
            y_str, suffix = date_str.split('-')
            suffix_int = int(suffix)
            if suffix_int > 12:
                ey = int(y_str[:2] + suffix)
                if suffix_int < int(y_str[2:]):
                    ey += 100
                return f"01/01/{y_str} - 12/31/{ey}"
            year, month = int(y_str), suffix_int
            last_day = get_last_day_of_month(year, month)
            return f"{month:02d}/01/{year} - {month:02d}/{last_day}/{year}"

        if re.match(r'\d{4}$', date_str):
            year = int(date_str)
            return f"01/01/{year} - 12/31/{year}"

        if re.match(r'\d{2}-\d{2}-\d{4}/\d{4}-\d{2}-\d{2}$', date_str):
            start_date, end_date = date_str.split('/')
            start_date_formatted = datetime.strptime(start_date, '%m-%d-%Y').strftime('%m/%d/%Y')
            end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
            return f"{start_date_formatted} - {end_date_formatted}"

        if re.match(r'\d{4}-\d{2}-\d{2} (To|TO|to) \d{4}-\d{2}-\d{2}', date_str):
            return convert_date_pattern(re.sub(r'\s+(To|TO|to)\s+', '/', date_str))
        m = re.search(
            r'(?i)\b(?P<kw>before|pre|ante|after|post)\.?\s*-?\s*'
            r'(?P<date>\d{1,2}/\d{1,2}/\d{4}|\d{4})\b',
            date_str)
        if m:
            kw = m.group('kw').lower()
            out_kw = 'after' if kw in {'after', 'post'} else 'before'
            raw = m.group('date')
            if '/' in raw:
                mo, d, y = raw.split('/')
                norm = f'{int(mo):02d}/{int(d):02d}/{y}'
            else:
                norm = f'01/01/{raw}' if out_kw == 'before' else f'12/31/{raw}'
            return f'{out_kw} {norm}'
        m = re.match(r'(circa|cir\.?|ca\.?|approx\.?|c\.?)\s*(\d{4})', date_str, re.IGNORECASE)
        if m:
            return f'circa {m.group(2)}'

        m = re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})',
                     date_str, re.IGNORECASE)
        if m:
            mo, y = m.groups()
            num = month_map[mo.capitalize()[:3]]
            last = get_last_day_of_month(int(y), int(num))
            return f"{num}/01/{y} - {num}/{last}/{y}"

        m = re.match(r'(\d{1,2})/0{1,2}/(\d{4})', date_str)
        if m:
            mo, y = m.groups()
            last = get_last_day_of_month(int(y), int(mo))
            return f"{int(mo):02d}/01/{y} - {int(mo):02d}/{last}/{y}"

        return date_str  # Return original if no match
    except Exception as e:
        return date_str  # Return original if any error occurs

# Function to apply transformations to the DataFrame
def process_dataframe(df, column):
    check_col_name = f'Check {column}'
    original_col_name = f'Original_{column}'

    # Save original values
    df[original_col_name] = df[column].copy()

    # Replace column with formatted values in-place
    df[column] = df[column].apply(
        lambda x: ensure_chronological_order(convert_date_pattern(str(x))) if pd.notna(x) else 'undated')

    # Create check column
    valid_patterns = [
        r'^\d{2}/\d{2}/\d{4}$',
        r'^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$',
        r'^undated$'
    ]
    def is_valid(s):
        return any(re.match(p, str(s)) for p in valid_patterns)
    df[check_col_name] = df[column].apply(lambda s: 'Yes' if not is_valid(s) else '')

    # Order columns: formatted column in place, Original_ and Check_ inserted immediately after
    cols = list(df.columns)
    for c in [original_col_name, check_col_name]:
        if c in cols:
            cols.remove(c)
    insert_pos = cols.index(column) + 1 if column in cols else len(cols)
    cols.insert(insert_pos, original_col_name)
    cols.insert(insert_pos + 1, check_col_name)
    df = df[cols]

    # Ensure RG column is padded to at least 4 chars (letter prefix preserved, e.g. W22 -> W022)
    if 'RG' in df.columns:
        df['RG'] = df['RG'].apply(lambda x: _pad_alnum(x, 4))

    # Ensure SubGr, Series, and SubSeries columns are padded to at least 3 chars
    for col in ['SubGr', 'SG', 'SubGroup', 'Series', 'SubSeries Number', 'Record Group Number', 'Subgroup Number', 'Series Number']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _pad_alnum(x, 3))

    return df

# Main script execution
file_path = select_file()
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
else:
    df = pd.read_excel(file_path)

column_to_format = select_column(df)
if column_to_format not in df.columns:
    messagebox.showerror("Error", f"The column '{column_to_format}' does not exist.")
    exit()

df = process_dataframe(df, column_to_format)

if file_path.endswith('.csv'):
    df.to_csv(file_path, index=False)
else:
    df.to_excel(file_path, index=False)

messagebox.showinfo("Completion", "Job completed successfully!")
root.destroy()



# TODO: move new column to the right of the original column - x
# TODO: ensure leap year is handled correctly - x
# TODO: resize tkinter window - x
# TODO: add headers for leading zeros - x
# TODO: fix 1776-1777 -> 1777/01/1776 - 1777/31/1776
# TODO: fix 1777-02-23/1777-04-25 -> 1777-02-23/1777-04-25
