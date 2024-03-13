import re
from datetime import datetime

def convert_strange_named_ranges(date_str):
    # Enhanced regex to handle both full and abbreviated month names, and optional end month and year
    matches = re.search(r'(\b[A-Za-z]+) (\d{1,2})( \d{4})? - (\b[A-Za-z]*\b)? ?(\d{1,2})( \d{4})?', date_str)
    if not matches:
        print(f"Could not process date range: {date_str}")
        return ""

    start_month, start_day, start_year_optional, end_month_optional, end_day, end_year_optional = matches.groups()

    # Determine the year to be used for the start date
    start_year = start_year_optional if start_year_optional else end_year_optional

    # If the end month is not provided, it implies the same month as the start month
    end_month = end_month_optional if end_month_optional else start_month

    # Reconstruct the date strings
    start_date_str = f"{start_month} {start_day} {start_year}"
    end_date_str = f"{end_month} {end_day} {end_year_optional}"

    # Safely parse the dates with a fallback for abbreviated month names
    for date_format in ("%B %d %Y", "%b %d %Y"):
        try:
            start_date = datetime.strptime(start_date_str, date_format)
            break
        except ValueError:
            continue
    else:
        print(f"Could not parse start date: {start_date_str}")
        return ""

    for date_format in ("%B %d %Y", "%b %d %Y"):
        try:
            end_date = datetime.strptime(end_date_str, date_format)
            break
        except ValueError:
            continue
    else:
        print(f"Could not parse end date: {end_date_str}")
        return ""

    # Convert dates to the desired format
    converted_start_date = start_date.strftime("%m/%d/%Y")
    converted_end_date = end_date.strftime("%m/%d/%Y")

    return f"{converted_start_date} - {converted_end_date}"

def process_file(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:  # Process non-empty lines
                    converted_date = convert_strange_named_ranges(line)
                    if converted_date:
                        print(converted_date)
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return

file_path = 'test.txt'
process_file(file_path)
