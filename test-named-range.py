import re
from datetime import datetime

def convert_date_format(date_str):
    # Identify and extract components from the date string
    # Accommodate date ranges where the start date might not include the year explicitly
    matches = re.search(r'(\b[A-Za-z]{3} \d{1,2})( \d{4})? - (\b[A-Za-z]{3} \d{1,2} \d{4})', date_str)
    if not matches:
        print(f"Could not process date range: {date_str}")
        return

    start_date_part, start_year, end_date_str = matches.groups()
    
    # If the year is missing from the start date, append the year from the end date
    if not start_year:
        end_year = re.search(r'\d{4}$', end_date_str).group()
        start_date_str = f"{start_date_part} {end_year}"
    else:
        start_date_str = f"{start_date_part}{start_year}"

    # Convert both start and end dates to the desired format
    start_date = datetime.strptime(start_date_str, "%b %d %Y")
    end_date = datetime.strptime(end_date_str, "%b %d %Y")

    converted_start_date = start_date.strftime("%m/%d/%Y")
    converted_end_date = end_date.strftime("%m/%d/%Y")

    return f"{converted_start_date} - {converted_end_date}"

def process_file(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:  # Ensure the line is not empty
                    converted_date = convert_date_format(line)
                    if converted_date:
                        print(converted_date)
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        return

# Replace 'your_file_path.txt' with the path to your text file
file_path = 'test.txt'
process_file(file_path)
