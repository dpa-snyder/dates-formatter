import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import threading
import re
from datetime import datetime, timedelta
import platform
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─── Shared helpers ───────────────────────────────────────────────────────────

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
    "Dec": "12", "December": "12",
}


def is_leap_year(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def get_last_day_of_month(year, month):
    if month == 2:
        return 29 if is_leap_year(year) else 28
    elif month in [4, 6, 9, 11]:
        return 30
    return 31


# ─── Single-date pipeline ─────────────────────────────────────────────────────

def format_single_date(date_str):
    """Return MM/DD/YYYY — first date of any range, or '' if not parseable."""
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


# ─── Range pipeline ───────────────────────────────────────────────────────────

def custom_format_date(date_str):
    """Return (formatted_str, flag) where flag is 'Yes' or ''."""
    try:
        def add_leading_zeros(d):
            d = re.sub(r'\b(\d{1})/(\d{1,2})/(\d{4})', r'0\1/\2/\3', d)
            d = re.sub(r'(\d{2})/(\d{1})/(\d{4})', r'\1/0\2/\3', d)
            return d

        date_str = re.sub(r'\s*\(.*?\)', '', date_str).strip()
        date_str = add_leading_zeros(date_str)

        if re.match(r'^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$', date_str):
            return (date_str, '')

        if re.fullmatch(r'\d{5}', date_str):
            serial = int(date_str)
            cur_os = platform.system()
            if cur_os == 'Darwin':
                d = datetime(1904, 1, 1) + timedelta(days=serial - 1)
            else:
                d = datetime(1899, 12, 31) + timedelta(days=serial)
            return (d.strftime('%m/%d/%Y'), 'Yes')

        m = re.fullmatch(r'^\d{4}([,;\s-]+\d{4}){1,}$', date_str)
        if m:
            years = sorted({int(y) for y in re.findall(r'\d{4}', date_str)})
            if len(years) > 1:
                return (f'01/01/{years[0]} - 12/31/{years[-1]}', 'Yes')

        m = re.match(r'([A-Za-z]+)\s(\d{1,2}),?\s(\d{4})\s[–-]\s([A-Za-z]+)\s(\d{1,2}),?\s(\d{4})', date_str)
        if m:
            sm, sd, sy, em, ed, ey = m.groups()
            return (f'{month_map[sm[:3].capitalize()]}/{sd.zfill(2)}/{sy} - '
                    f'{month_map[em[:3].capitalize()]}/{ed.zfill(2)}/{ey}', '')

        m = re.match(r'([A-Za-z]+)\s(\d{1,2}),\s(\d{4})\s-\s([A-Za-z]+)\s(\d{1,2}),\s(\d{4})', date_str)
        if m:
            sm, sd, sy, em, ed, ey = m.groups()
            return (f'{month_map[sm[:3]]}/{sd.zfill(2)}/{sy} - '
                    f'{month_map[em[:3]]}/{ed.zfill(2)}/{ey}', '')

        m = re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*'
                     r'(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})', date_str, re.IGNORECASE)
        if m:
            mon, day, year = m.groups()
            return (f'{month_map[mon.capitalize()[:3]]}/{day.zfill(2)}/{year}', '')

        m = re.match(r'(\d{4})\s+(vol|volume)\b.*', date_str, re.IGNORECASE)
        if m:
            return (f'01/01/{m.group(1)} - 12/31/{m.group(1)}', 'Yes')

        if re.search(r'\b(N\.?\s*D\.?|n\.?\s*d\.?|U\.?\s*D\.?|u\.?\s*d\.?|No Date|not dated)\b',
                     date_str, re.IGNORECASE):
            return ('undated', '')

        m = re.match(r'(\d{5})? ?- ?(\d{5})?', date_str)
        if m:
            ss, es = m.groups()
            cur_os = platform.system()
            base = datetime(1899, 12, 31) if cur_os == 'Windows' else (
                datetime(1904, 1, 1) if cur_os == 'Darwin' else datetime(1899, 12, 31))

            def conv(serial):
                if not serial:
                    return None
                n = int(serial)
                if cur_os == 'Darwin':
                    return (base + timedelta(days=n - 1)).strftime('%m/%d/%Y')
                return (base + timedelta(days=n)).strftime('%m/%d/%Y')

            sd, ed = conv(ss), conv(es)
            if sd and ed:
                return (f'{sd} - {ed}', '')
            elif sd:
                return (sd, 'Yes')
            elif ed:
                return (ed, 'Yes')

        m = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
        if m:
            y, mo, d = m.groups()
            return (f'{int(mo):02d}/{int(d):02d}/{y}', '')

        for pat, fmt in [
            (r'(?i)\bpost[- ]*(\d{4})\b', 'after {year}'),
            (r'(?i)\bpre[- ]*(\d{4})\b', 'before {year}'),
            (r'(?i)\bante\.?[- ]*(\d{4})\b', 'before {year}'),
        ]:
            m = re.search(pat, date_str)
            if m:
                return (fmt.format(year=m.group(1)), 'Yes')

        if re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', date_str):
            return (datetime.strptime(date_str.split()[0], '%Y-%m-%d').strftime('%m/%d/%Y'), '')

        m = re.match(r'(\d{4})\s*-\s*(\d{4})', date_str)
        if m:
            return (f'01/01/{m.group(1)} - 12/31/{m.group(2)}', '')

        m = re.match(r'(\d{4})/(\d{2}) - (\d{4})/(\d{2})', date_str)
        if m:
            sy, smo, ey, emo = m.groups()
            last = get_last_day_of_month(int(ey), int(emo))
            return (f'{smo}/01/{sy} - {emo}/{last}/{ey}', '')

        m = re.match(r'(\d{4})-(\d{2})', date_str)
        if m:
            sy, ety = m.groups()
            ef = int(sy[:2] + ety)
            if int(ety) < int(sy[2:]):
                ef += 100
            return (f'01/01/{sy} - 12/31/{ef}', '')

        for pat, action in [
            (r'^\?{1,2} - (\d{1,2})/(\d{1,2})/(\d{4})$',
             lambda mo, d, y: f'before {int(mo):02d}/{int(d):02d}/{y}'),
            (r'^\?{1,2} - (\d{4})$',
             lambda y: f'before {y}'),
            (r'(\d{1,2})/(\d{1,2})/(\d{4}) - \?{1,2}$',
             lambda mo, d, y: f'after {int(mo):02d}/{int(d):02d}/{y}'),
        ]:
            m = re.match(pat, date_str)
            if m:
                return (action(*m.groups()), 'Yes')

        m = re.match(r'(\d{1,2})/0{1,2}/(\d{4}) - (\d{1,2})/0{1,2}/(\d{4})', date_str)
        if m:
            ms, ys, _, ye = m.groups()
            last = get_last_day_of_month(int(ys), int(ms))
            return (f'{int(ms):02d}/01/{ys} - {int(ms):02d}/{last}/{ys}', '')

        m = re.match(r'(\d{1,2})/0{1,2}/(\d{4})', date_str)
        if m:
            mo, y = m.groups()
            last = get_last_day_of_month(int(y), int(mo))
            return (f'{int(mo):02d}/01/{y} - {int(mo):02d}/{last}/{y}', '')

        m = re.match(r'(\d{1,2})//(\d{4})', date_str)
        if m:
            mo, y = m.groups()
            last = get_last_day_of_month(int(y), int(mo))
            return (f'{int(mo):02d}/01/{y} - {int(mo):02d}/{last}/{y}', '')

        if ' - ' in date_str:
            sd, ed = date_str.split(' - ', 1)
            try:
                if '??' in sd or '??' in ed or '00' in sd or '00' in ed:
                    ms, _, ys = sd.split('/')
                    me, _, ye = ed.split('/')
                    if ms.isdigit() and ys.isdigit():
                        last = get_last_day_of_month(int(ys), int(ms))
                        return (f'{int(ms):02d}/01/{ys} - {int(me):02d}/{last}/{ye}', '')
                    return (date_str, '')
                sdf = datetime.strptime(sd, '%m/%d/%Y').strftime('%m/%d/%Y')
                edf = datetime.strptime(ed, '%m/%d/%Y').strftime('%m/%d/%Y')
                return (f'{sdf} - {edf}', '')
            except ValueError:
                return (date_str, '')
        else:
            try:
                return (datetime.strptime(date_str, '%m/%d/%Y').strftime('%m/%d/%Y'), '')
            except ValueError:
                pass

        m = re.match(r'(circa|cir\.?|ca\.?|approx\.?|c\.?)\s*(\d{4})', date_str, re.IGNORECASE)
        if m:
            return (f'circa {m.group(2)}', 'Yes')

        if re.match(r'(\d{4})s?(-\d{4})?', date_str):
            if '-' in date_str:
                sy, ey = date_str.split('-', 1)
                return (f'01/01/{sy} - 12/31/{ey}', '')
            elif 's' in date_str:
                y = date_str.rstrip('s')
                return (f'01/01/{y} - 12/31/{int(y)+9}', '')
            else:
                return (f'01/01/{date_str} - 12/31/{date_str}', '')

        if '??' in date_str:
            if date_str.count('/') == 2:
                mo, day, y = date_str.split('/')
                if day == '??':
                    return (f'{mo}/01/{y} - {mo}/{get_last_day_of_month(int(y), int(mo))}/{y}', '')
                return (date_str, '')
            elif date_str.startswith('??/'):
                y = date_str.split('/')[1]
                return (f'01/01/{y} - 12/31/{y}', '')

        m = re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})',
                     date_str, re.IGNORECASE)
        if m:
            mo, y = m.groups()
            num = month_map[mo.capitalize()[:3]]
            last = get_last_day_of_month(int(y), int(num))
            return (f'{num}/01/{y} - {num}/{last}/{y}', '')

        m = re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[-.]\s*(\d{2})',
                     date_str, re.IGNORECASE)
        if m:
            mo, y2 = m.groups()
            y = f'19{y2}' if int(y2) < 50 else f'20{y2}'
            num = month_map[mo.capitalize()[:3]]
            last = get_last_day_of_month(int(y), int(num))
            return (f'{num}/01/{y} - {num}/{last}/{y}', '')

        m = re.match(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)'
            r'\s+(\d{1,2})\s+(?:-|)\s*(?:\1\s+)?(\d{1,2})\s+(\d{4})',
            date_str, re.IGNORECASE)
        if m:
            mname, sd, ed, y = m.groups()
            num = month_map[mname.capitalize()]
            return (f'{num}/{sd.zfill(2)}/{y} - {num}/{ed.zfill(2)}/{y}', '')

        return (date_str, 'Yes')

    except Exception:
        return (date_str, 'Yes')


def convert_strange_named_ranges(date_str):
    m = re.search(r'(\b[A-Za-z]+) (\d{1,2})( \d{4})? - (\b[A-Za-z]*\b)? ?(\d{1,2})( \d{4})?', date_str)
    if not m:
        return date_str
    sm, sd, sy_opt, em_opt, ed, ey_opt = m.groups()
    sy = sy_opt or ey_opt
    em = em_opt or sm
    for fmt in ('%B %d %Y', '%b %d %Y'):
        try:
            start = datetime.strptime(f'{sm} {sd} {sy}', fmt)
            break
        except ValueError:
            continue
    else:
        return date_str
    for fmt in ('%B %d %Y', '%b %d %Y'):
        try:
            end = datetime.strptime(f'{em} {ed} {ey_opt}', fmt)
            break
        except ValueError:
            continue
    else:
        return date_str
    return f'{start.strftime("%m/%d/%Y")} - {end.strftime("%m/%d/%Y")}'


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


def is_valid_date_format(date_str):
    return any(re.match(p, str(date_str)) for p in [
        r'^\d{2}/\d{2}/\d{4}$',
        r'^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$',
        r'^undated$',
    ])


# ─── Dublin Core pipeline ─────────────────────────────────────────────────────

def convert_date_pattern(date_str):
    try:
        if re.match(r'\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}', date_str):
            return date_str
        date_str = re.sub(r'\s*\(.*?\)', '', date_str).strip()
        if re.match(r'\d{4}-\d{2}-\d{2}$', date_str):
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%m/%d/%Y')
        if re.match(r'\d{4}-\d{4}$', date_str):
            sy, ey = map(int, date_str.split('-'))
            return f'01/01/{sy} - 12/31/{ey}'
        if re.match(r'\d{4}/\d{4}-\d{2}$', date_str):
            sy, ep = date_str.split('/')
            ey, emo = map(int, ep.split('-'))
            return f'01/01/{sy} - {emo:02d}/{get_last_day_of_month(ey, emo)}/{ey}'
        if re.match(r'\d{4}-\d{2}/\d{4}$', date_str):
            sp, ey = date_str.split('/')
            sy, smo = map(int, sp.split('-'))
            return f'{smo:02d}/01/{sy} - 12/31/{ey}'
        if re.match(r'\d{4}-\d{2}/\d{4}-\d{2}$', date_str):
            sp, ep = date_str.split('/')
            sy, smo = map(int, sp.split('-'))
            ey, emo = map(int, ep.split('-'))
            return (f'{smo:02d}/01/{sy} - '
                    f'{emo:02d}/{get_last_day_of_month(ey, emo)}/{ey}')
        if re.match(r'\d{4}/\d{4}(?:/\d{4})*', date_str):
            years = list(map(int, date_str.split('/')))
            return f'01/01/{years[0]} - 12/31/{years[-1]}'
        if re.match(r'\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$', date_str):
            sd, ed = date_str.split('/')
            return (f'{datetime.strptime(sd, "%Y-%m-%d").strftime("%m/%d/%Y")} - '
                    f'{datetime.strptime(ed, "%Y-%m-%d").strftime("%m/%d/%Y")}')
        if re.match(r'\d{4}-\d{2}$', date_str):
            y_str, suffix = date_str.split('-')
            suffix_int = int(suffix)
            if suffix_int > 12:
                ey = int(y_str[:2] + suffix)
                if suffix_int < int(y_str[2:]):
                    ey += 100
                return f'01/01/{y_str} - 12/31/{ey}'
            y, mo = int(y_str), suffix_int
            return f'{mo:02d}/01/{y} - {mo:02d}/{get_last_day_of_month(y, mo)}/{y}'
        if re.match(r'\d{4}$', date_str):
            y = int(date_str)
            return f'01/01/{y} - 12/31/{y}'
        if re.match(r'\d{2}-\d{2}-\d{4}/\d{4}-\d{2}-\d{2}$', date_str):
            sd, ed = date_str.split('/')
            return (f'{datetime.strptime(sd, "%m-%d-%Y").strftime("%m/%d/%Y")} - '
                    f'{datetime.strptime(ed, "%Y-%m-%d").strftime("%m/%d/%Y")}')
        if re.match(r'\d{4}-\d{2}-\d{2} (To|TO|to) \d{4}-\d{2}-\d{2}', date_str):
            return convert_date_pattern(
                date_str.replace('To', '-').replace('TO', '-').replace('to', '-'))
        m = re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})',
                     date_str, re.IGNORECASE)
        if m:
            mo, y = m.groups()
            num = month_map[mo.capitalize()[:3]]
            last = get_last_day_of_month(int(y), int(num))
            return f'{num}/01/{y} - {num}/{last}/{y}'
        m = re.match(r'(\d{1,2})/0{1,2}/(\d{4})', date_str)
        if m:
            mo, y = m.groups()
            last = get_last_day_of_month(int(y), int(mo))
            return f'{int(mo):02d}/01/{y} - {int(mo):02d}/{last}/{y}'
        return date_str
    except Exception:
        return date_str


# ─── Shared column post-processing ───────────────────────────────────────────

def apply_leading_zeros(df):
    if 'RG' in df.columns:
        df['RG'] = df['RG'].apply(
            lambda x: f'{int(x):04d}' if pd.notna(x) and x != '' else x)
    for col in ['SubGr', 'SG', 'SubGroup', 'Series', 'SubSeries Number',
                'Record Group Number', 'Subgroup Number', 'Series Number']:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: f'{int(x):03d}' if pd.notna(x) and x != '' else x)
    return df


def reorder_columns(df, column, original_col, check_col):
    cols = list(df.columns)
    for c in [original_col, check_col]:
        if c in cols:
            cols.remove(c)
    pos = cols.index(column) + 1 if column in cols else len(cols)
    cols.insert(pos, original_col)
    cols.insert(pos + 1, check_col)
    return df[cols]


# ─── GUI ─────────────────────────────────────────────────────────────────────

MODES = ["Single Date", "Date Range", "Dublin Core"]

MODE_SUFFIXES = {
    "Single Date": "single",
    "Date Range":  "range",
    "Dublin Core": "dublin-core",
}

MODE_DESCRIPTIONS = {
    "Single Date": "MM/DD/YYYY",
    "Date Range":  "MM/DD/YYYY – MM/DD/YYYY",
    "Dublin Core": "Dublin Core-compatible",
}


class DateFormatterApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Date Formatter")
        self.geometry("600x560")
        self.resizable(False, False)
        self.df = None
        self.file_path = None
        self._build_ui()

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(self, text="Date Formatter",
                     font=ctk.CTkFont(size=24, weight="bold")
                     ).grid(row=0, column=0, padx=30, pady=(28, 2), sticky="w")

        ctk.CTkLabel(self, text="Normalize date columns in Excel and CSV files.",
                     font=ctk.CTkFont(size=13), text_color="gray"
                     ).grid(row=1, column=0, padx=30, pady=(0, 20), sticky="w")

        # ── Output formats ──
        ctk.CTkLabel(self, text="Output Format(s)",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=2, column=0, padx=30, pady=(0, 8), sticky="w")

        cb_frame = ctk.CTkFrame(self, fg_color="transparent")
        cb_frame.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="w")

        self.mode_vars = {}
        for i, mode in enumerate(MODES):
            var = ctk.BooleanVar(value=(mode == "Single Date"))
            self.mode_vars[mode] = var
            cb = ctk.CTkCheckBox(
                cb_frame, text=f"{mode}  —  {MODE_DESCRIPTIONS[mode]}",
                variable=var, command=self._check_run_state)
            cb.grid(row=i, column=0, pady=4, sticky="w")

        # ── File ──
        ctk.CTkLabel(self, text="File",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=4, column=0, padx=30, pady=(0, 6), sticky="w")

        file_frame = ctk.CTkFrame(self, fg_color="transparent")
        file_frame.grid(row=5, column=0, padx=30, pady=(0, 20), sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)

        self.file_entry = ctk.CTkEntry(
            file_frame, placeholder_text="No file selected",
            state="disabled", height=38)
        self.file_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(file_frame, text="Browse", width=110, height=38,
                      command=self._browse
                      ).grid(row=0, column=1)

        # ── Column ──
        ctk.CTkLabel(self, text="Column to Format",
                     font=ctk.CTkFont(size=13, weight="bold")
                     ).grid(row=6, column=0, padx=30, pady=(0, 6), sticky="w")

        self.col_menu = ctk.CTkOptionMenu(
            self, values=["Load a file first"],
            width=540, height=38, state="disabled")
        self.col_menu.grid(row=7, column=0, padx=30, pady=(0, 24), sticky="w")

        # ── Run ──
        self.run_btn = ctk.CTkButton(
            self, text="Run", height=46, width=540,
            font=ctk.CTkFont(size=15, weight="bold"),
            state="disabled", command=self._run)
        self.run_btn.grid(row=8, column=0, padx=30, pady=(0, 18))

        # ── Progress ──
        self.progress_bar = ctk.CTkProgressBar(self, width=540)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=9, column=0, padx=30, pady=(0, 8))

        self.status_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), text_color="gray")
        self.status_lbl.grid(row=10, column=0, padx=30, pady=(0, 24), sticky="w")

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _check_run_state(self):
        any_checked = any(v.get() for v in self.mode_vars.values())
        if self.df is not None and any_checked:
            self.run_btn.configure(state="normal")
        else:
            self.run_btn.configure(state="disabled")

    def _browse(self):
        path = filedialog.askopenfilename()
        if not path:
            return
        try:
            df = pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{e}")
            return

        self.df = df
        self.file_path = path

        self.file_entry.configure(state="normal")
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, os.path.basename(path))
        self.file_entry.configure(state="disabled")

        cols = list(df.columns)
        self.col_menu.configure(values=cols, state="normal")
        self.col_menu.set(cols[0])
        self._check_run_state()
        self._set_status(0, f"{len(df):,} rows loaded — ready.")

    def _run(self):
        selected = [m for m in MODES if self.mode_vars[m].get()]
        if not selected:
            return
        column = self.col_menu.get()
        self.run_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self._set_status(0, "Starting…")
        threading.Thread(
            target=self._run_all, args=(column, selected), daemon=True).start()

    # ── Processing (background thread) ───────────────────────────────────────

    def _run_all(self, column, modes):
        try:
            n = len(modes)
            results = []
            for i, mode in enumerate(modes):
                p_start = i / n
                p_end   = (i + 1) / n
                out_path, flagged, total = self._process_mode(
                    column, mode, p_start, p_end)
                results.append((mode, out_path, flagged, total))
            self.after(0, self._finish_all, results)
        except Exception as e:
            self.after(0, self._error, str(e))

    def _process_mode(self, column, mode, p_start, p_end):
        df = self.df.copy()
        total = len(df)
        tick  = max(1, total // 100)

        original_col = f'Original_{column}'
        check_col    = f'Check {column}'

        df[original_col] = df[column].copy()

        p_range = p_end - p_start

        def progress(frac, text):
            self.after(0, self._set_status, p_start + frac * p_range, text)

        # ── Single Date ──────────────────────────────────────────────────────
        if mode == "Single Date":
            results = []
            for i, val in enumerate(df[column]):
                results.append(format_single_date(str(val)) if pd.notna(val) else '')
                if i % tick == 0:
                    progress(0.05 + (i / total) * 0.80,
                             f"[Single] row {i+1:,} of {total:,}…")
            df[column] = results
            pat = re.compile(r'^\d{2}/\d{2}/\d{4}$')
            df[check_col] = df[column].apply(
                lambda s: 'Yes' if not isinstance(s, str) or not pat.match(s) else '')

        # ── Date Range ───────────────────────────────────────────────────────
        elif mode == "Date Range":
            formatted, flags = [], []
            for i, val in enumerate(df[column]):
                v, f = custom_format_date(str(val)) if pd.notna(val) else ('undated', '')
                formatted.append(v)
                flags.append(f)
                if i % tick == 0:
                    progress(0.05 + (i / total) * 0.55,
                             f"[Range] row {i+1:,} of {total:,}…")
            df[column]    = formatted
            df[check_col] = flags

            progress(0.65, "[Range] resolving named ranges…")
            df[column] = df[column].apply(convert_strange_named_ranges)

            progress(0.75, "[Range] checking chronological order…")
            df[column] = df[column].apply(ensure_chronological_order)

            df[check_col] = df.apply(
                lambda r: 'Yes' if not is_valid_date_format(r[column])
                          and r[check_col] != 'Yes' else r[check_col], axis=1)
            df[check_col] = df.apply(
                lambda r: 'Yes' if isinstance(r[original_col], str)
                          and ';' in r[original_col]
                          and r[check_col] != 'Yes' else r[check_col], axis=1)

        # ── Dublin Core ──────────────────────────────────────────────────────
        elif mode == "Dublin Core":
            results = []
            for i, val in enumerate(df[column]):
                results.append(
                    ensure_chronological_order(convert_date_pattern(str(val))) if pd.notna(val) else 'undated')
                if i % tick == 0:
                    progress(0.05 + (i / total) * 0.80,
                             f"[Dublin Core] row {i+1:,} of {total:,}…")
            df[column] = results
            dc_valid = [
                r'^\d{2}/\d{2}/\d{4}$',
                r'^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$',
                r'^undated$',
            ]
            df[check_col] = df[column].apply(
                lambda s: 'Yes' if not any(re.match(p, str(s)) for p in dc_valid) else '')

        progress(0.88, f"[{mode}] reordering columns…")
        df = reorder_columns(df, column, original_col, check_col)

        progress(0.93, f"[{mode}] applying archive leading zeros…")
        df = apply_leading_zeros(df)

        # Output file: original_name_suffix.ext
        base, ext = os.path.splitext(self.file_path)
        suffix   = MODE_SUFFIXES[mode]
        out_path = f"{base}_{suffix}{ext}"

        progress(0.97, f"[{mode}] saving {os.path.basename(out_path)}…")
        if out_path.endswith('.csv'):
            df.to_csv(out_path, index=False)
        else:
            df.to_excel(out_path, index=False)

        flagged = int((df[check_col] == 'Yes').sum())
        return out_path, flagged, total

    # ── UI state helpers ──────────────────────────────────────────────────────

    def _set_status(self, progress, text):
        self.progress_bar.set(progress)
        self.status_lbl.configure(text=text)

    def _finish_all(self, results):
        self.run_btn.configure(state="normal")
        self.progress_bar.set(1.0)
        parts = [f"{MODE_SUFFIXES[m]}: {f:,} flagged" for m, _, f, _ in results]
        total = results[0][3] if results else 0
        self.status_lbl.configure(
            text=f"Done — {total:,} rows  |  " + "  |  ".join(parts))

    def _error(self, msg):
        self.run_btn.configure(state="normal")
        self._set_status(0, "Error — see dialog.")
        messagebox.showerror("Error", msg)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = DateFormatterApp()
    app.mainloop()
