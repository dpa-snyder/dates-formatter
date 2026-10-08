import  pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
import time
import re
from datetime import datetime, timedelta
import platform
import os
import stat
import tempfile


def strip_parenthetical_notes(text):
    """Remove same-line parenthetical notes without rescanning failed suffixes."""
    output = []
    pending = None
    whitespace_start = 0
    for char in text:
        if pending is not None:
            if char == ')':
                del output[whitespace_start:]
                pending = None
            elif char == '\n':
                output.extend(pending)
                output.append(char)
                pending = None
            else:
                pending.append(char)
        elif char == '(':
            whitespace_start = len(output)
            while whitespace_start and output[whitespace_start - 1].isspace():
                whitespace_start -= 1
            pending = ['(']
        else:
            output.append(char)
    if pending is not None:
        output.extend(pending)
    return ''.join(output)


class WindowsOutputDirectory:
    """Use directory and file handles; never reopen a staged output by name."""
    def __init__(self, path):
        import ctypes
        from ctypes import wintypes
        import msvcrt
        self.ctypes = ctypes
        self.msvcrt = msvcrt
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.native = ctypes.WinDLL('ntdll')
        class UnicodeString(ctypes.Structure):
            _fields_ = [('Length', wintypes.USHORT), ('MaximumLength', wintypes.USHORT),
                        ('Buffer', wintypes.LPWSTR)]
        class ObjectAttributes(ctypes.Structure):
            _fields_ = [('Length', wintypes.ULONG), ('RootDirectory', wintypes.HANDLE),
                        ('ObjectName', ctypes.POINTER(UnicodeString)),
                        ('Attributes', wintypes.ULONG), ('SecurityDescriptor', wintypes.LPVOID),
                        ('SecurityQualityOfService', wintypes.LPVOID)]
        class IOStatus(ctypes.Structure):
            _fields_ = [('Status', ctypes.c_void_p), ('Information', ctypes.c_size_t)]
        class FileInfo(ctypes.Structure):
            _fields_ = [('Attributes', wintypes.DWORD), ('Creation', wintypes.FILETIME),
                        ('Access', wintypes.FILETIME), ('Write', wintypes.FILETIME),
                        ('Volume', wintypes.DWORD), ('SizeHigh', wintypes.DWORD),
                        ('SizeLow', wintypes.DWORD), ('Links', wintypes.DWORD),
                        ('IndexHigh', wintypes.DWORD), ('IndexLow', wintypes.DWORD)]
        self.UnicodeString, self.ObjectAttributes = UnicodeString, ObjectAttributes
        self.IOStatus, self.FileInfo = IOStatus, FileInfo
        self.kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                            wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
                                            wintypes.HANDLE]
        self.kernel.CreateFileW.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(FileInfo)]
        self.native.NtCreateFile.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
            ctypes.POINTER(ObjectAttributes), ctypes.POINTER(IOStatus), wintypes.LPVOID,
            wintypes.ULONG, wintypes.ULONG, wintypes.ULONG, wintypes.ULONG,
            wintypes.LPVOID, wintypes.ULONG]
        self.native.NtCreateFile.restype = wintypes.LONG
        self.native.NtSetInformationFile.argtypes = [wintypes.HANDLE, ctypes.POINTER(IOStatus),
            wintypes.LPVOID, wintypes.ULONG, wintypes.ULONG]
        self.native.NtSetInformationFile.restype = wintypes.LONG
        self.native.RtlNtStatusToDosError.argtypes = [wintypes.LONG]
        self.native.RtlNtStatusToDosError.restype = wintypes.ULONG
        self.handle = self.kernel.CreateFileW(path, 0x80000000, 7, None, 3, 0x02000000, None)
        if self.handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())

    def _check(self, status):
        if status < 0:
            raise self.ctypes.WinError(self.native.RtlNtStatusToDosError(status))

    def _info(self, handle):
        info = self.FileInfo()
        if not self.kernel.GetFileInformationByHandle(handle, self.ctypes.byref(info)):
            raise self.ctypes.WinError(self.ctypes.get_last_error())
        return info

    def identity(self):
        info = self._info(self.handle)
        return info.Volume, info.IndexHigh, info.IndexLow

    def open_file(self, name, create=False):
        from ctypes import wintypes
        c = self.ctypes
        text = c.create_unicode_buffer(name)
        byte_length = len(name.encode('utf-16-le'))
        value = self.UnicodeString(byte_length, byte_length + 2, c.cast(text, wintypes.LPWSTR))
        attrs = self.ObjectAttributes(c.sizeof(self.ObjectAttributes), self.handle,
                                     c.pointer(value), 0x40, None, None)
        handle = wintypes.HANDLE()
        # A staged handle has DELETE access and no sharing, so its name cannot be
        # substituted and its contents cannot be changed before publication.
        access = 0x12019f | 0x10000 if create else 0x120089
        status = self.native.NtCreateFile(c.byref(handle), access, c.byref(attrs),
            c.byref(self.IOStatus()), None, 0x80, 0 if create else 7,
            2 if create else 1, 0x20 | 0x40 | 0x00200000, None, 0)
        self._check(status)
        try:
            if self._info(handle).Attributes & (0x10 | 0x400):
                raise ValueError("File must be regular, not a link or directory.")
            fd = self.msvcrt.open_osfhandle(handle.value,
                (os.O_RDWR if create else os.O_RDONLY) | os.O_BINARY)
        except BaseException:
            self.kernel.CloseHandle(handle)
            raise
        return fd

    def publish(self, fd, name):
        from ctypes import wintypes
        c = self.ctypes
        class RenameInfo(c.Structure):
            _fields_ = [('Replace', wintypes.BOOLEAN), ('Root', wintypes.HANDLE),
                        ('Length', wintypes.ULONG), ('Name', wintypes.WCHAR * (len(name.encode('utf-16-le')) // 2 + 1))]
        info = RenameInfo()
        info.Replace, info.Root = 1, self.handle
        info.Length, info.Name = len(name.encode('utf-16-le')), name
        # Native rename accepts a directory handle; SetFileInformationByHandle's
        # Win32 form requires RootDirectory=NULL and would re-resolve the path.
        self._check(self.native.NtSetInformationFile(self.msvcrt.get_osfhandle(fd),
            c.byref(self.IOStatus()), c.byref(info), c.sizeof(info), 10))

    def discard(self, fd):
        c = self.ctypes
        delete = c.c_ubyte(1)
        self._check(self.native.NtSetInformationFile(self.msvcrt.get_osfhandle(fd),
            c.byref(self.IOStatus()), c.byref(delete), c.sizeof(delete), 13))

    def close(self):
        self.kernel.CloseHandle(self.handle)


class OutputDirectory:
    """Anchor all reads and saves to one opened parent directory."""
    def __init__(self, path):
        self.path = os.path.dirname(os.path.abspath(os.fspath(path)))
        self.windows = WindowsOutputDirectory(self.path) if os.name == 'nt' else None
        self.fd = None if self.windows else os.open(self.path, os.O_RDONLY | os.O_DIRECTORY)

    def identity(self):
        if self.windows:
            return self.windows.identity()
        info = os.fstat(self.fd)
        return info.st_dev, info.st_ino

    def open_input(self, name):
        if self.windows:
            fd = self.windows.open_file(name)
        else:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("Input must be a regular file.")
            return os.fdopen(fd, 'rb')
        except BaseException:
            os.close(fd)
            raise

    def target_info(self, name):
        try:
            if self.windows:
                fd = self.windows.open_file(name)
                try:
                    return os.fstat(fd)
                finally:
                    os.close(fd)
            info = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Output must be a regular file, not a link or directory.")
        return info

    def close(self):
        if self.windows:
            self.windows.close()
        else:
            os.close(self.fd)


def load_dataframe(path, **options):
    directory = OutputDirectory(path)
    try:
        with directory.open_input(os.path.basename(os.fspath(path))) as source:
            reader = pd.read_csv if os.fspath(path).lower().endswith('.csv') else pd.read_excel
            return reader(source, **options), directory.identity()
    finally:
        directory.close()


def save_dataframe(df, path, expected_directory=None):
    """Write privately, then publish into the opened directory without following links."""
    path = os.fspath(path)
    directory = OutputDirectory(path)
    private_fd = fd = None
    private_name = temporary_name = None
    published = False
    try:
        if expected_directory is not None and directory.identity() != expected_directory:
            raise OSError("The selected directory changed. Reload the file before saving.")
        name = os.path.basename(path)
        target = directory.target_info(name)
        if directory.windows:
            import secrets
            temporary_name = '.date-formatter-' + secrets.token_hex(16) + '.tmp'
            fd = directory.windows.open_file(temporary_name, create=True)
        else:
            import secrets
            private_name = '.date-formatter-' + secrets.token_hex(16)
            os.mkdir(private_name, 0o700, dir_fd=directory.fd)
            private_fd = os.open(private_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                 dir_fd=directory.fd)
            info = os.fstat(private_fd)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise OSError("Temporary output directory is not private.")
            temporary_name = 'output'
            fd = os.open(temporary_name, os.O_RDWR | os.O_CREAT | os.O_EXCL,
                         0o600, dir_fd=private_fd)
            if target is not None:
                os.fchown(fd, target.st_uid, target.st_gid)
                os.fchmod(fd, stat.S_IMODE(target.st_mode))
        # Keep the original descriptor open through publication. The stream owns
        # a duplicate, avoiding any reopened pathname or released Windows handle.
        is_csv = path.lower().endswith('.csv')
        options = {'encoding': 'utf-8', 'newline': ''} if is_csv else {}
        with os.fdopen(os.dup(fd), 'w' if is_csv else 'w+b', **options) as output:
            if is_csv:
                df.to_csv(output, index=False)
            else:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                    for worksheet in writer.sheets.values():
                        for row in worksheet.iter_rows():
                            for cell in row:
                                if isinstance(cell.value, str):
                                    cell.data_type = 's'
                                    cell.number_format = '@'
            output.flush()
            os.fsync(output.fileno())
        directory.target_info(name)  # Refuse a nonregular destination before commit.
        if directory.windows:
            directory.windows.publish(fd, name)
        else:
            os.replace(temporary_name, name, src_dir_fd=private_fd, dst_dir_fd=directory.fd)
        published = True
    finally:
        try:
            if fd is not None:
                try:
                    if directory.windows and not published:
                        directory.windows.discard(fd)
                finally:
                    os.close(fd)
            if private_fd is not None:
                try:
                    if not published and temporary_name is not None:
                        os.unlink(temporary_name, dir_fd=private_fd)
                except FileNotFoundError:
                    pass
                finally:
                    os.close(private_fd)
            if private_name is not None:
                try:
                    os.rmdir(private_name, dir_fd=directory.fd)
                except OSError:
                    pass  # Another process may have moved the directory; never recurse.
        finally:
            directory.close()

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
    try:
        file_path = askopenfilename()
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
df, directory_info = load_dataframe(file_path)


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
        date_str = strip_parenthetical_notes(date_str).strip()
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
                return (f'01/01/{start_year} - 12/31/{end_year}', 'Yes')

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
            return (f'01/01/{year} - 12/31/{year}', 'Yes')

        # N.D., n.d., nd, No Date, not dated, U.D., u.d., ud
        if re.search(r'\b(N\.?\s*D\.?|n\.?\s*d\.?|U\.?\s*D\.?|u\.?\s*d\.?|No Date|not dated)\b', date_str, re.IGNORECASE):
            return ('undated', '')

        # Handle excel 5-digit serial date ranges or incomplete ranges
        excel_serial_range_pattern = r'(\d{5})? ?- ?(\d{5})?'
        match = re.match(excel_serial_range_pattern, date_str)
        
        if match:
            start_serial, end_serial = match.groups()

            # Detect the operating system to determine the Excel start date
            current_os = platform.system()

            if current_os == 'Windows':
                excel_start_date = datetime(1899, 12, 31)
            elif current_os == 'Darwin':
                excel_start_date = datetime(1904, 1, 1)
            else:
                excel_start_date = datetime(1899, 12, 31)


            def convert_serial(serial):
                if not serial:
                    return None
                serial_int = int(serial)
                if current_os == 'Darwin':
                    return (excel_start_date + timedelta(days=serial_int - 1)).strftime('%m/%d/%Y')
                return (excel_start_date + timedelta(days=serial_int)).strftime('%m/%d/%Y')

            # Convert start and end serial numbers to dates
            start_date = convert_serial(start_serial)
            end_date = convert_serial(end_serial)

            # Handle various cases based on what was present in the input
            if start_date and end_date:
                return (f'{start_date} - {end_date}', '')
            elif start_date:
                return (f'{start_date}', 'Yes')  # Incomplete end
            elif end_date:
                return (f'{end_date}', 'Yes')  # Incomplete start

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
                return (format_str.format(year=year), 'Yes')

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
                return (action(*match.groups()), 'Yes')

        # Handling dates with a single '0' day part for range inputs 'MM/0/YYYY - MM/0/YYYY'
        range_zero_day_regex = r'(\d{1,2})/0{1,2}/(\d{4}) - (\d{1,2})/0{1,2}/(\d{4})'
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
        single_zero_dd_regex = r'(\d{1,2})/0{1,2}/(\d{4})'
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
            return (f'circa {year}', 'Yes')

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
        return (date_str, 'Yes')

    except Exception as e:
        return (date_str, 'Yes')


# Single-date formatter: returns MM/DD/YYYY or '' if unparseable
def format_single_date(date_str: str) -> str:
    """Return MM/DD/YYYY for the first date of any range, or '' if not parseable."""
    if date_str is None:
        return ''
    s = str(date_str).strip()
    if s == '' or s.lower() in {'undated', 'n.d.', 'nd', 'n d', 'no date'}:
        return ''
    try:
        result, _ = custom_format_date(s)
        result = ensure_chronological_order(result)
        if ' - ' in result:
            return result.split(' - ')[0]
        if re.match(r'^\d{2}/\d{2}/\d{4}$', result):
            return result
    except Exception:
        pass
    return ''


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
check_col_name = f'Check {column_to_format}'

# Apply custom_format_date to create the new column and Check Me column
df['temp'] = df[column_to_format].apply(lambda cell: custom_format_date(str(cell)) if pd.notna(cell) else ('undated', ''))
df[new_column_name], df[check_col_name] = zip(*df['temp'])
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

# Analyze the new_column_name column and update the check column
df[check_col_name] = df.apply(lambda row: 'Yes' if not is_valid_date_format(row[new_column_name]) and row[check_col_name] != 'Yes' else row[check_col_name], axis=1)

# Create a strict single-date column 'formatted_date' (MM/DD/YYYY only) from the original input column
df['formatted_date'] = df[column_to_format].apply(lambda s: format_single_date(str(s)) if pd.notna(s) else '')

# Ensure 'formatted_date' appears immediately after the original input column
cols = list(df.columns)
if 'formatted_date' in cols:
    cols.remove('formatted_date')
    insert_at = cols.index(column_to_format) + 1 if column_to_format in cols else len(cols)
    cols.insert(insert_at, 'formatted_date')
    df = df[cols]

# Recompute check column: 'Yes' if formatted_date is empty or not strictly MM/DD/YYYY
mmddyyyy_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
df[check_col_name] = df['formatted_date'].apply(lambda s: 'Yes' if not isinstance(s, str) or not mmddyyyy_pattern.match(s) else '')

# Copy original input into 'Original_{input}' and replace input with formatted value
original_col_name = f'Original_{column_to_format}'
if original_col_name not in df.columns:
    df[original_col_name] = df[column_to_format]
else:
    df[original_col_name] = df[column_to_format]

# Replace input column with the normalized single date
df[column_to_format] = df['formatted_date']

# Remove the old wide formatted range/text column and the helper 'formatted_date'
if new_column_name in df.columns:
    df.drop(columns=[new_column_name], inplace=True)
if 'formatted_date' in df.columns:
    df.drop(columns=['formatted_date'], inplace=True)

# Ensure final order: Original_{input}, {input}, Check {input}, then the rest
cols = list(df.columns)
for c in [original_col_name, check_col_name]:
    if c in cols:
        cols.remove(c)
insert_pos = cols.index(column_to_format) + 1 if column_to_format in cols else len(cols)
cols.insert(insert_pos, original_col_name)
cols.insert(insert_pos + 1, check_col_name)
df = df[cols]

# Ensure RG column is formatted with at least 4 digits
if 'RG' in df.columns:
    df['RG'] = df['RG'].apply(lambda x: f'{int(x):04d}' if pd.notna(x) and x != '' else x)

# Ensure SubGr, Series, and SubSeries columns are formatted with at least 3 digits
for col in ['SubGr', 'SG', 'SubGroup', 'Series', 'SubSeries Number']:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: f'{int(x):03d}' if pd.notna(x) and x != '' else x)

# Save the DataFrame back to the file
save_dataframe(df, file_path, directory_info)

# Update progress bar after writing back to the file
update_progress_bar(progress_bar, 100)

# Show completion message
messagebox.showinfo("Completion", "Job completed successfully!")
progress_win.destroy()
