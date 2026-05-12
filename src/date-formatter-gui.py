try:
    import customtkinter as ctk
except Exception:  # Allows parser/test imports on systems without Tk.
    class _CTkStub:
        CTk = object

        @staticmethod
        def set_appearance_mode(_mode):
            return None

        @staticmethod
        def set_default_color_theme(_theme):
            return None

    ctk = _CTkStub()
try:
    from tkinter import filedialog, messagebox, Toplevel
except Exception:
    class _FileDialogStub:
        @staticmethod
        def askopenfilename(*args, **kwargs):
            raise RuntimeError("Tkinter is unavailable in this environment.")

    class _MessageBoxStub:
        @staticmethod
        def showerror(*args, **kwargs):
            raise RuntimeError("Tkinter is unavailable in this environment.")

        @staticmethod
        def askretrycancel(*args, **kwargs):
            return False

    class _ToplevelStub:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Tkinter is unavailable in this environment.")

    filedialog = _FileDialogStub()
    messagebox = _MessageBoxStub()
    Toplevel = _ToplevelStub
import pandas as pd
import threading
import re
import json
import logging
import tempfile
import time
import traceback
import webbrowser
import subprocess
import sys
from datetime import datetime, timedelta
import os

APP_VERSION = "2026.05.11"

MANUAL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "user-manual.html")

LOG_PATH = os.path.join(tempfile.gettempdir(), "date-formatter.log")
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dates-formatter-settings.json")
DEFAULT_SETTINGS = {
    "theme": "dark",             # "dark" | "light" | "system"
    "geometry": None,            # "WxH+X+Y" or None
    "recent_files": [],          # most-recent first, capped at 5
    "output_mode": "overwrite",  # "overwrite" | "copy"
}


def load_settings():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {**DEFAULT_SETTINGS, **data}
    except (OSError, json.JSONDecodeError):
        pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError as e:
        logging.warning("Could not save settings to %s: %s", SETTINGS_PATH, e)


SETTINGS = load_settings()
THEME_MODE = SETTINGS["theme"] if SETTINGS["theme"] in {"dark", "light", "system"} else "dark"

ctk.set_appearance_mode(THEME_MODE)
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


def is_plausible_year_text(value):
    return bool(re.fullmatch(r'\d{4}', value)) and 1000 <= int(value) <= 2100


def is_excel_serial_text(value):
    return bool(re.fullmatch(r'\d{5}', value))


def excel_serial_to_date(serial_text):
    return (datetime(1899, 12, 31) + timedelta(days=int(serial_text))).strftime('%m/%d/%Y')


# ─── Single-date pipeline ─────────────────────────────────────────────────────

def format_single_date(date_str):
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

        if is_plausible_year_text(date_str):
            return (f'01/01/{date_str} - 12/31/{date_str}', '')

        if is_excel_serial_text(date_str):
            return (excel_serial_to_date(date_str), 'Yes')

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

        m = re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})$',
                     date_str, re.IGNORECASE)
        if m:
            mo, y = m.groups()
            num = month_map[mo.capitalize()[:3]]
            last = get_last_day_of_month(int(y), int(num))
            return (f'{num}/01/{y} - {num}/{last}/{y}', '')

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

        m = re.fullmatch(r'(\d{5})?\s*-\s*(\d{5})?', date_str)
        if m:
            ss, es = m.groups()

            def conv(serial):
                if not serial:
                    return None
                return excel_serial_to_date(serial)

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
            return (f'{out_kw} {norm}', 'Yes')

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
            ms, ys, me, ye = m.groups()
            start = f'{int(ms):02d}/01/{ys}'
            end_last = get_last_day_of_month(int(ye), int(me))
            end = f'{int(me):02d}/{end_last}/{ye}'
            return (f'{start} - {end}', '')

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
                    if all(x.isdigit() for x in [ms, ys, me, ye]):
                        last = get_last_day_of_month(int(ye), int(me))
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

        if re.fullmatch(r'(\d{4})s?(-\d{4})?', date_str):
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
        if re.search(r'\b(N\.?\s*D\.?|n\.?\s*d\.?|U\.?\s*D\.?|u\.?\s*d\.?|No Date|not dated)\b',
                     date_str, re.IGNORECASE):
            return 'undated'
        if re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$', date_str):
            return datetime.strptime(date_str.split()[0], '%Y-%m-%d').strftime('%m/%d/%Y')
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

def _pad_alnum(val, width):
    """Pad numeric portion of an ID to `width` total chars.

    Pure numerics get zero-padded. A single leading letter is preserved
    and the digits after it get padded so the total length is `width`.
    Unknown shapes are returned unchanged rather than crashing.
    """
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


def apply_leading_zeros(df):
    if 'RG' in df.columns:
        df['RG'] = df['RG'].apply(lambda x: _pad_alnum(x, 4))
    for col in ['SubGr', 'SG', 'SubGroup', 'Series', 'SubSeries Number',
                'Record Group Number', 'Subgroup Number', 'Series Number']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: _pad_alnum(x, 3))
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

MODE_TITLE = {
    "Single Date": "Single Date",
    "Date Range":  "ArchivERA",
    "Dublin Core": "Dublin Core",
}

MODE_ICON = {
    "Single Date": "📅",
    "Date Range":  "📆",
    "Dublin Core": "🗂",
}

MODE_OUTPUT_EXAMPLE = {
    "Single Date": "MM/DD/YYYY",
    "Date Range":  "MM/DD/YYYY - MM/DD/YYYY",
    "Dublin Core": "MM/DD/YYYY (from DC/ISO)",
}

MODE_HELP = {
    "Single Date": "Output a single date. Ranges collapse to the start date.",
    "Date Range":  "Output a date range. Single dates pass through.",
    "Dublin Core": "Convert Dublin Core or ISO inputs.",
}

MODE_TOOLTIP = {
    "Single Date": "Best when each row should resolve to one specific date.",
    "Date Range":  "Best when each row represents a span of time. Use this for ArchivERA imports.",
    "Dublin Core": "Best when input uses Dublin Core or ISO format (YYYY-MM-DD, YYYY/YYYY, etc.).",
}

THEME_LABELS = {"light": "Light", "dark": "Dark", "system": "Auto"}
THEME_VALUES = {v: k for k, v in THEME_LABELS.items()}

OUTPUT_LABELS = {"overwrite": "Overwrite original", "copy": "Save as copy"}
OUTPUT_VALUES = {v: k for k, v in OUTPUT_LABELS.items()}

STEPS = ["Mode", "File", "Columns", "Run"]


class Tooltip:
    """Small hover tooltip. Attaches to any tk/CTk widget."""

    def __init__(self, widget, text, delay=450):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id = None
        self._tip = None
        try:
            widget.bind("<Enter>", self._schedule, add="+")
            widget.bind("<Leave>", self._hide, add="+")
            widget.bind("<ButtonPress>", self._hide, add="+")
        except Exception:
            pass

    def _schedule(self, _e=None):
        self._cancel()
        try:
            self._after_id = self.widget.after(self.delay, self._show)
        except Exception:
            pass

    def _cancel(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip:
            return
        try:
            x = self.widget.winfo_rootx() + 16
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
            self._tip = Toplevel(self.widget)
            self._tip.wm_overrideredirect(True)
            self._tip.wm_geometry(f"+{x}+{y}")
            frame = ctk.CTkFrame(
                self._tip, corner_radius=6,
                fg_color=("gray85", "gray22"),
                border_width=1, border_color=("gray70", "gray35"))
            frame.pack()
            ctk.CTkLabel(
                frame, text=self.text,
                text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=11),
                wraplength=320, justify="left"
            ).pack(padx=10, pady=6)
        except Exception:
            self._tip = None

    def _hide(self, _e=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class DateFormatterApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Date Formatter")
        self.ui_scale = self._compute_ui_scale()
        self._apply_ui_scale()
        self._set_window_geometry()
        self.resizable(True, True)

        # State
        self.df = None
        self.file_path = None
        self.col_vars = {}
        self._col_checkboxes = {}
        self._mode_cards = {}
        self._step_widgets = []
        self._geom_after = None

        self._build_ui()
        self._refresh_recent_files()
        self._update_stepper(1)

        self.bind("<Configure>", self._on_configure)

    def _compute_ui_scale(self):
        """Blend screen-height and DPI scaling into a stable UI scale."""
        screen_h = self.winfo_screenheight()
        resolution_scale = screen_h / 1080.0
        try:
            tk_dpi_scale = float(self.tk.call("tk", "scaling")) / 1.3333333333
        except Exception:
            tk_dpi_scale = 1.0
        blended = (resolution_scale * 0.65) + (tk_dpi_scale * 0.35)
        return max(0.95, min(1.35, blended))

    def _apply_ui_scale(self):
        try:
            ctk.set_widget_scaling(self.ui_scale)
        except Exception:
            pass

    def _font(self, size, weight="normal"):
        scaled = int(round(size * self.ui_scale))
        scaled = max(10, min(40, scaled))
        return ctk.CTkFont(size=scaled, weight=weight)

    def _mono_font(self, size):
        scaled = int(round(size * self.ui_scale))
        scaled = max(10, min(40, scaled))
        return ctk.CTkFont(family="TkFixedFont", size=scaled)

    def _set_window_geometry(self):
        """Restore saved window state if any. Otherwise scale to desktop."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        saved = SETTINGS.get("geometry")
        if isinstance(saved, str):
            m = re.match(r'^(\d+)x(\d+)([+-]\d+)([+-]\d+)$', saved)
            if m:
                w, h, x, y = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                w = max(720, min(w, screen_w))
                h = max(820, min(h, screen_h))
                x = max(0, min(x, max(0, screen_w - 100)))
                y = max(0, min(y, max(0, screen_h - 100)))
                self.geometry(f"{w}x{h}+{x}+{y}")
                self.minsize(720, 820)
                return

        width = max(760, min(1100, int(screen_w * 0.72)))
        height = max(840, min(960, int(screen_h * 0.90)))
        x = max(0, (screen_w - width) // 2)
        y = 0
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(720, 820)

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        p = ctk.CTkScrollableFrame(self, fg_color="transparent")
        p.grid(row=0, column=0, sticky="nsew")
        p.grid_columnconfigure(0, weight=1)

        self._build_header(p, row=0)
        self._build_stepper(p, row=1)
        self._build_mode_card(p, row=2)
        self._build_file_card(p, row=3)
        self._build_columns_card(p, row=4)
        self._build_output_card(p, row=5)
        self._build_run_section(p, row=6)
        self._build_status_panel(p, row=7)
        self._build_footer(p, row=8)

    # ── Header (title + subtitle + theme segmented) ──

    def _build_header(self, parent, row):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=row, column=0, padx=28, pady=(24, 4), sticky="ew")
        bar.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            bar, text="Date Formatter",
            font=self._font(26, "bold"))
        title.grid(row=0, column=0, sticky="w")

        self.theme_seg = ctk.CTkSegmentedButton(
            bar, values=["Light", "Dark", "Auto"],
            command=self._on_theme_change,
            font=self._font(11))
        self.theme_seg.set(THEME_LABELS.get(THEME_MODE, "Dark"))
        self.theme_seg.grid(row=0, column=1, sticky="e")
        Tooltip(self.theme_seg, "Light, Dark, or Auto (follow system).")

        ctk.CTkLabel(
            parent, text="Standardize date columns in Excel and CSV spreadsheets.",
            font=self._font(13), text_color=("gray45", "gray60")
        ).grid(row=row, column=0, padx=28, pady=(38, 18), sticky="w")

    # ── Stepper (1 Mode → 2 File → 3 Columns → 4 Run) ──

    def _build_stepper(self, parent, row):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=0, padx=28, pady=(0, 18), sticky="ew")

        self._step_widgets = []
        col = 0
        for i, label in enumerate(STEPS):
            if i > 0:
                line = ctk.CTkFrame(
                    wrap, height=2, fg_color=("gray80", "gray30"))
                line.grid(row=0, column=col, sticky="ew", padx=8, pady=(13, 0))
                wrap.grid_columnconfigure(col, weight=1)
                col += 1

            step_col = ctk.CTkFrame(wrap, fg_color="transparent")
            step_col.grid(row=0, column=col)
            circle = ctk.CTkLabel(
                step_col, text=str(i + 1),
                width=30, height=30, corner_radius=15,
                fg_color=("gray85", "gray25"),
                text_color=("gray30", "gray70"),
                font=self._font(13, "bold"))
            circle.pack()
            ctk.CTkLabel(
                step_col, text=label,
                font=self._font(11),
                text_color=("gray40", "gray60")
            ).pack(pady=(4, 0))
            self._step_widgets.append(circle)
            col += 1

    def _update_stepper(self, active):
        for i, w in enumerate(self._step_widgets):
            idx = i + 1
            if idx < active:
                w.configure(
                    fg_color=("#2d5db8", "#7cb0ff"),
                    text_color=("white", "#0e1116"),
                    text="✓")
            elif idx == active:
                w.configure(
                    fg_color=("#2d5db8", "#7cb0ff"),
                    text_color=("white", "#0e1116"),
                    text=str(idx))
            else:
                w.configure(
                    fg_color=("gray85", "gray25"),
                    text_color=("gray30", "gray70"),
                    text=str(idx))

    # ── Card scaffolding ──

    def _make_card(self, parent, row, title, icon):
        card = ctk.CTkFrame(
            parent, corner_radius=12,
            fg_color=("gray97", "gray14"),
            border_width=1,
            border_color=("gray85", "gray22"))
        card.grid(row=row, column=0, padx=28, pady=(0, 14), sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, padx=18, pady=(14, 4), sticky="ew")
        ctk.CTkLabel(
            header, text=f"{icon}  {title}",
            font=self._font(13, "bold")
        ).pack(anchor="w")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.grid(row=1, column=0, padx=18, pady=(2, 16), sticky="ew")
        body.grid_columnconfigure(0, weight=1)
        return body

    # ── Mode card (with 3 clickable sub-cards) ──

    def _build_mode_card(self, parent, row):
        body = self._make_card(parent, row, "Conversion Type", "🎯")

        self.mode_var = ctk.StringVar(value="Single Date")
        self._mode_cards = {}

        cards_row = ctk.CTkFrame(body, fg_color="transparent")
        cards_row.grid(row=0, column=0, sticky="ew")
        for i in range(len(MODES)):
            cards_row.grid_columnconfigure(i, weight=1, uniform="modecards")

        for i, mode in enumerate(MODES):
            self._make_mode_card(cards_row, mode, i)

    def _make_mode_card(self, parent, mode, col):
        selected = (self.mode_var.get() == mode)
        card = ctk.CTkFrame(
            parent, corner_radius=10,
            fg_color=self._mode_fg(selected),
            border_width=2,
            border_color=self._mode_border(selected))
        card.grid(row=0, column=col, padx=4, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)

        icon_lbl = ctk.CTkLabel(
            inner, text=MODE_ICON[mode], font=self._font(22))
        icon_lbl.pack(anchor="w")
        title_lbl = ctk.CTkLabel(
            inner, text=MODE_TITLE[mode], font=self._font(14, "bold"))
        title_lbl.pack(anchor="w", pady=(4, 2))
        out_lbl = ctk.CTkLabel(
            inner, text=MODE_OUTPUT_EXAMPLE[mode],
            font=self._mono_font(11),
            text_color=("gray40", "gray60"))
        out_lbl.pack(anchor="w")
        help_lbl = ctk.CTkLabel(
            inner, text=MODE_HELP[mode],
            font=self._font(11),
            text_color=("gray35", "gray65"),
            wraplength=200, justify="left")
        help_lbl.pack(anchor="w", pady=(8, 0))

        def select(_e=None, m=mode):
            self.mode_var.set(m)
            self._refresh_mode_cards()
            self._on_state_change()
            self._update_mismatch_hint()

        for w in (card, inner, icon_lbl, title_lbl, out_lbl, help_lbl):
            w.bind("<Button-1>", select)
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass

        Tooltip(card, MODE_TOOLTIP[mode])
        self._mode_cards[mode] = card

    def _mode_fg(self, selected):
        return ("#e7eefb", "#1a2741") if selected else ("gray100", "gray16")

    def _mode_border(self, selected):
        return ("#2d5db8", "#7cb0ff") if selected else ("gray85", "gray25")

    def _refresh_mode_cards(self):
        current = self.mode_var.get()
        for mode, card in self._mode_cards.items():
            sel = (mode == current)
            card.configure(
                fg_color=self._mode_fg(sel),
                border_color=self._mode_border(sel))

    # ── File card (browse + recent files) ──

    def _build_file_card(self, parent, row):
        body = self._make_card(parent, row, "File", "📄")

        file_row = ctk.CTkFrame(body, fg_color="transparent")
        file_row.grid(row=0, column=0, sticky="ew")
        file_row.grid_columnconfigure(0, weight=1)

        self.file_entry = ctk.CTkEntry(
            file_row, placeholder_text="No file selected",
            state="disabled", height=36)
        self.file_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        browse_btn = ctk.CTkButton(
            file_row, text="Browse", width=110, height=36,
            command=self._browse)
        browse_btn.grid(row=0, column=1)
        Tooltip(browse_btn, "Pick an Excel (.xlsx) or CSV file.")

        self._recent_frame = ctk.CTkFrame(body, fg_color="transparent")
        self._recent_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

    def _refresh_recent_files(self):
        for w in self._recent_frame.winfo_children():
            w.destroy()
        recent = [p for p in SETTINGS.get("recent_files", []) if os.path.exists(p)]
        if not recent:
            return
        ctk.CTkLabel(
            self._recent_frame, text="Recent:",
            font=self._font(11), text_color=("gray45", "gray60")
        ).pack(side="left", padx=(0, 6))
        for p in recent:
            name = os.path.basename(p)
            btn = ctk.CTkButton(
                self._recent_frame, text=name, height=24,
                fg_color="transparent", border_width=1,
                text_color=("gray20", "gray80"),
                hover_color=("gray85", "gray25"),
                font=self._font(11),
                command=lambda pp=p: self._load_file(pp))
            btn.pack(side="left", padx=2)
            Tooltip(btn, p)

    # ── Columns card (search + checkbox list) ──

    def _build_columns_card(self, parent, row):
        body = self._make_card(parent, row, "Columns to Format", "☑")

        self.col_search_var = ctk.StringVar()
        self.col_search_var.trace_add("write", lambda *_: self._refresh_columns())

        search_entry = ctk.CTkEntry(
            body, textvariable=self.col_search_var,
            placeholder_text="🔍  Search columns…",
            height=32)
        search_entry.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        Tooltip(search_entry, "Filter the list below. Case-insensitive.")

        self.col_frame = ctk.CTkScrollableFrame(body, height=140)
        self.col_frame.grid(row=1, column=0, sticky="ew")
        self.col_frame.grid_columnconfigure(0, weight=1)
        self._col_placeholder = ctk.CTkLabel(
            self.col_frame, text="Load a file first.",
            text_color=("gray45", "gray60"))
        self._col_placeholder.grid(row=0, column=0, pady=6, sticky="w")

        self._hint_label = ctk.CTkLabel(
            body, text="", font=self._font(11),
            text_color=("#b35900", "#f0a060"),
            wraplength=600, justify="left")
        self._hint_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self._hint_label.grid_remove()

    def _refresh_columns(self):
        if not self._col_checkboxes:
            return
        q = self.col_search_var.get().strip().lower()
        visible = 0
        for col, cb in self._col_checkboxes.items():
            if not q or q in col.lower():
                cb.grid(row=visible, column=0, sticky="w", pady=2)
                visible += 1
            else:
                cb.grid_remove()

    # ── Output card (overwrite vs save copy) ──

    def _build_output_card(self, parent, row):
        body = self._make_card(parent, row, "Output", "💾")

        current = SETTINGS.get("output_mode", "overwrite")
        if current not in OUTPUT_LABELS:
            current = "overwrite"

        self.output_seg = ctk.CTkSegmentedButton(
            body,
            values=[OUTPUT_LABELS["overwrite"], OUTPUT_LABELS["copy"]],
            command=self._on_output_mode_change,
            font=self._font(12))
        self.output_seg.set(OUTPUT_LABELS[current])
        self.output_seg.grid(row=0, column=0, sticky="ew")
        Tooltip(
            self.output_seg,
            "Overwrite original: replaces the file you loaded. "
            "Save as copy: writes a new file named "
            "{original}_formatted.{ext} in the same folder.")

        self._output_hint = ctk.CTkLabel(
            body, text="", font=self._font(11),
            text_color=("gray45", "gray60"))
        self._output_hint.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self._update_output_hint()

    def _update_output_hint(self):
        mode = SETTINGS.get("output_mode", "overwrite")
        if mode == "copy" and self.file_path:
            root, ext = os.path.splitext(self.file_path)
            self._output_hint.configure(
                text=f"Will save to {os.path.basename(root)}_formatted{ext}")
        elif mode == "copy":
            self._output_hint.configure(
                text="Will save a new file named {original}_formatted.{ext}")
        elif self.file_path:
            self._output_hint.configure(
                text=f"Will overwrite {os.path.basename(self.file_path)}")
        else:
            self._output_hint.configure(
                text="Original columns are preserved as Original_{column}.")

    # ── Run + progress ──

    def _build_run_section(self, parent, row):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=0, padx=28, pady=(6, 14), sticky="ew")
        wrap.grid_columnconfigure(0, weight=1)

        self.run_btn = ctk.CTkButton(
            wrap, text="▶  Run Conversion", height=46,
            font=self._font(15, "bold"),
            state="disabled", command=self._run)
        self.run_btn.grid(row=0, column=0, sticky="ew")
        Tooltip(
            self.run_btn,
            "Process the selected columns. Disabled until a file and "
            "at least one column are selected.")

        self.progress_bar = ctk.CTkProgressBar(wrap, height=8)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(12, 0))

    # ── Status panel (rolling log) ──

    def _build_status_panel(self, parent, row):
        body = self._make_card(parent, row, "Status", "📊")
        self.status_box = ctk.CTkTextbox(
            body, height=90,
            font=self._mono_font(11),
            fg_color=("gray96", "gray11"),
            border_width=1, border_color=("gray85", "gray22"),
            wrap="none")
        self.status_box.grid(row=0, column=0, sticky="ew")
        self.status_box.configure(state="disabled")

    def _log(self, text, level="info"):
        prefix = {"info": "  ", "ok": "✓ ", "warn": "⚠ ", "err": "✕ "}.get(level, "  ")
        try:
            self.status_box.configure(state="normal")
            self.status_box.insert("end", f"{prefix}{text}\n")
            self.status_box.see("end")
            self.status_box.configure(state="disabled")
        except Exception:
            pass

    # ── Footer ──

    def _build_footer(self, parent, row):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.grid(row=row, column=0, padx=28, pady=(2, 24), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer, text=f"v{APP_VERSION}",
            font=self._font(10),
            text_color=("gray55", "gray45")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            footer, text="📖  View User Manual",
            height=32, fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            font=self._font(12),
            command=self._open_manual
        ).grid(row=0, column=1, sticky="e")

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _open_manual(self):
        if not os.path.exists(MANUAL_PATH):
            messagebox.showerror(
                "Manual not found",
                f"Expected user-manual.html at:\n{MANUAL_PATH}\n\n"
                "Ask your IT Admin to redeploy with the manual file.")
            return
        try:
            webbrowser.open(f"file://{MANUAL_PATH}")
        except Exception as e:
            logging.error("Failed to open manual: %s", e)
            messagebox.showerror("Could not open manual", str(e))

    def _on_theme_change(self, label):
        val = THEME_VALUES.get(label, "dark")
        try:
            ctk.set_appearance_mode(val if val != "system" else "system")
        except Exception:
            pass
        SETTINGS["theme"] = val
        save_settings(SETTINGS)
        self._refresh_mode_cards()

    def _on_output_mode_change(self, label):
        val = OUTPUT_VALUES.get(label, "overwrite")
        SETTINGS["output_mode"] = val
        save_settings(SETTINGS)
        self._update_output_hint()

    def _on_configure(self, event):
        if event.widget is not self:
            return
        if self._geom_after is not None:
            try:
                self.after_cancel(self._geom_after)
            except Exception:
                pass
        self._geom_after = self.after(500, self._save_geometry)

    def _save_geometry(self):
        try:
            geom = self.geometry()
            SETTINGS["geometry"] = geom
            save_settings(SETTINGS)
        except Exception as e:
            logging.warning("Could not persist window geometry: %s", e)

    def _on_state_change(self):
        has_file = self.df is not None
        any_col = any(v.get() for v in self.col_vars.values())
        ready = has_file and any_col
        self.run_btn.configure(state="normal" if ready else "disabled")

        if not has_file:
            self._update_stepper(2)
        elif not any_col:
            self._update_stepper(3)
        else:
            self._update_stepper(4)

        self._update_mismatch_hint()
        self._update_output_hint()

    def _browse(self):
        path = filedialog.askopenfilename(
            filetypes=[("Spreadsheets", "*.xlsx *.csv"),
                       ("Excel", "*.xlsx"),
                       ("CSV", "*.csv"),
                       ("All files", "*.*")])
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path):
        try:
            if path.endswith('.csv'):
                df = pd.read_csv(path, dtype=str, keep_default_na=False)
            else:
                df = pd.read_excel(path, dtype=str, keep_default_na=False)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file:\n{e}")
            return

        self.df = df
        self.file_path = path

        self.file_entry.configure(state="normal")
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, os.path.basename(path))
        self.file_entry.configure(state="disabled")

        # Rebuild column checkboxes
        for widget in self.col_frame.winfo_children():
            widget.destroy()
        self.col_vars = {}
        self._col_checkboxes = {}
        for i, col in enumerate(df.columns):
            var = ctk.BooleanVar(value=False)
            self.col_vars[col] = var
            cb = ctk.CTkCheckBox(
                self.col_frame, text=col,
                variable=var, command=self._on_state_change)
            cb.grid(row=i, column=0, pady=2, sticky="w")
            self._col_checkboxes[col] = cb
        self.col_search_var.set("")

        self._push_recent(path)
        self._refresh_recent_files()
        self._log(f"Loaded {os.path.basename(path)} ({len(df):,} rows, "
                  f"{len(df.columns)} columns).", "ok")
        self._on_state_change()
        self.progress_bar.set(0)

    def _push_recent(self, path):
        rec = [p for p in SETTINGS.get("recent_files", []) if p != path]
        rec.insert(0, path)
        SETTINGS["recent_files"] = rec[:5]
        save_settings(SETTINGS)

    def _open_path(self, path):
        if not path:
            return
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            logging.error("Could not open %s: %s", path, e)
            messagebox.showerror("Could not open", f"{path}\n\n{e}")

    # ── Mode/column mismatch hint ──

    def _detect_likely_mode(self, col_name):
        if self.df is None or col_name not in self.df.columns:
            return None
        samples = []
        for v in self.df[col_name].astype(str):
            s = v.strip()
            if s:
                samples.append(s)
            if len(samples) >= 50:
                break
        if not samples:
            return None

        range_pat = re.compile(r'\d{1,2}/\d{1,2}/\d{4}\s*-\s*\d{1,2}/\d{1,2}/\d{4}')
        single_pat = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')
        year_pat = re.compile(r'^\d{4}$')
        iso_pat = re.compile(r'^\d{4}-\d{2}(-\d{2})?(/.+)?$')

        ranges = sum(1 for s in samples if range_pat.search(s))
        singles = sum(1 for s in samples if single_pat.match(s))
        isos = sum(1 for s in samples if iso_pat.match(s))
        years = sum(1 for s in samples if year_pat.match(s))
        total = len(samples)

        if isos / total > 0.5:
            return "Dublin Core"
        if ranges / total > 0.4:
            return "Date Range"
        if years / total > 0.5:
            return "Date Range"
        if singles / total > 0.5:
            return "Single Date"
        return None

    def _update_mismatch_hint(self):
        if not hasattr(self, "_hint_label"):
            return
        mode = self.mode_var.get()
        cols = [c for c, v in self.col_vars.items() if v.get()]
        if not cols:
            self._hint_label.grid_remove()
            return
        likely = self._detect_likely_mode(cols[0])
        if likely and likely != mode:
            self._hint_label.configure(
                text=(f"Heads up: values in '{cols[0]}' look like a better "
                      f"fit for {likely} mode. Currently using {mode}."))
            self._hint_label.grid()
        else:
            self._hint_label.grid_remove()

    def _run(self):
        mode    = self.mode_var.get()
        columns = [col for col, var in self.col_vars.items() if var.get()]
        if not columns:
            return
        self.run_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self._log(f"Run start. Mode: {mode}. Columns: {', '.join(columns)}.")
        threading.Thread(
            target=self._run_all, args=(columns, mode), daemon=True).start()

    # ── Processing (background thread) ───────────────────────────────────────

    def _output_path(self):
        if SETTINGS.get("output_mode") == "copy" and self.file_path:
            root, ext = os.path.splitext(self.file_path)
            return f"{root}_formatted{ext}"
        return self.file_path

    def _run_all(self, columns, mode):
        logging.info("Run start: mode=%s columns=%s file=%s",
                     mode, columns, self.file_path)
        start = time.monotonic()
        out_path = self._output_path()
        try:
            df = self.df.copy()
            n  = len(columns)
            total_flagged = 0
            for i, column in enumerate(columns):
                self.after(0, self._log,
                           f"Processing {column} ({i+1}/{n})…", "info")
                df, flagged = self._process_column(
                    df, column, mode, i / n, (i + 1) / n)
                total_flagged += flagged

            self.after(0, self._log,
                       f"Saving to {os.path.basename(out_path)}…", "info")
            self.after(0, self.progress_bar.set, 0.97)
            self._save_with_retry(df, out_path)
            elapsed = time.monotonic() - start
            logging.info("Run done: rows=%d flagged=%d", len(df), total_flagged)
            self.after(0, self._finish_all,
                       mode, total_flagged, len(df), n, out_path, elapsed)
        except RuntimeError as e:
            logging.warning("Run cancelled or non-fatal: %s", e)
            self.after(0, self._log, str(e), "warn")
            self.after(0, self.progress_bar.set, 0)
            self.after(0, lambda: self.run_btn.configure(state="normal"))
        except Exception as e:
            logging.error("Unhandled exception during run:\n%s",
                          traceback.format_exc())
            self.after(0, self._error, f"{e}\n\nDetails logged to: {LOG_PATH}")

    def _process_column(self, df, column, mode, p_start, p_end):
        total = len(df)
        tick  = max(1, total // 100)

        original_col = f'Original_{column}'
        check_col    = f'Check {column}'
        df[original_col] = df[column].copy()

        p_range = p_end - p_start

        def progress(frac):
            self.after(0, self.progress_bar.set, p_start + frac * p_range)

        # ── Single Date ──────────────────────────────────────────────────────
        if mode == "Single Date":
            results = []
            for i, val in enumerate(df[column]):
                results.append(format_single_date(val) if val else '')
                if i % tick == 0:
                    progress(0.05 + (i / total) * 0.80)
            df[column] = results
            pat = re.compile(r'^\d{2}/\d{2}/\d{4}$')
            df[check_col] = df[column].apply(
                lambda s: 'Yes' if not isinstance(s, str) or not pat.match(s) else '')

        # ── Date Range ───────────────────────────────────────────────────────
        elif mode == "Date Range":
            formatted, flags = [], []
            for i, val in enumerate(df[column]):
                v, f = custom_format_date(val) if val else ('undated', '')
                formatted.append(v)
                flags.append(f)
                if i % tick == 0:
                    progress(0.05 + (i / total) * 0.55)
            df[column]    = formatted
            df[check_col] = flags

            progress(0.65)
            df[column] = df[column].apply(convert_strange_named_ranges)

            progress(0.75)
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
                    ensure_chronological_order(
                        convert_date_pattern(val)) if val else 'undated')
                if i % tick == 0:
                    progress(0.05 + (i / total) * 0.80)
            df[column] = results
            dc_valid = [
                r'^\d{2}/\d{2}/\d{4}$',
                r'^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$',
                r'^undated$',
            ]
            df[check_col] = df[column].apply(
                lambda s: 'Yes' if not any(re.match(p, str(s)) for p in dc_valid) else '')

        progress(0.88)
        df = reorder_columns(df, column, original_col, check_col)

        progress(0.93)
        df = apply_leading_zeros(df)

        flagged = int((df[check_col] == 'Yes').sum())
        return df, flagged

    def _save_with_retry(self, df, path):
        """Save df to path, retrying if the file is locked (e.g. open in Excel)."""
        event = threading.Event()
        result = [True]

        while True:
            try:
                if path.endswith('.csv'):
                    df.to_csv(path, index=False)
                else:
                    with pd.ExcelWriter(path, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                        ws = writer.sheets[next(iter(writer.sheets))]
                        for row in ws.iter_rows(min_row=2):
                            for cell in row:
                                cell.number_format = '@'
                return
            except PermissionError:
                event.clear()

                def ask(event=event, result=result):
                    ans = messagebox.askretrycancel(
                        "File in use",
                        f"{os.path.basename(path)} appears to be open.\n"
                        "Please close it and click Retry."
                    )
                    result[0] = ans
                    event.set()

                self.after(0, ask)
                event.wait()
                if not result[0]:
                    raise RuntimeError("Save cancelled.")

    # ── UI state helpers ──────────────────────────────────────────────────────

    def _finish_all(self, mode, flagged, total, n_cols, out_path, elapsed):
        self.run_btn.configure(state="normal")
        self.progress_bar.set(1.0)
        if flagged:
            self._log(f"Done. {flagged:,} of {total:,} rows flagged for review.", "warn")
        else:
            self._log(f"Done. {total:,} rows processed, no rows flagged.", "ok")
        self._show_completion_dialog(mode, flagged, total, n_cols, out_path, elapsed)

    def _show_completion_dialog(self, mode, flagged, total, n_cols, out_path, elapsed):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Conversion complete")
        dlg.transient(self)
        dlg.resizable(False, False)
        try:
            dlg.grab_set()
        except Exception:
            pass

        ctk.CTkLabel(
            dlg, text="✓", font=self._font(36),
            text_color=("#1f8a3d", "#3fc35f")
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            dlg, text="Conversion complete",
            font=self._font(18, "bold")
        ).pack(pady=(0, 12))

        body = ctk.CTkFrame(dlg, fg_color="transparent")
        body.pack(fill="x", padx=28, pady=(0, 12))
        body.grid_columnconfigure(1, weight=1)

        rows = [
            ("Mode", mode),
            ("Rows processed", f"{total:,}"),
            ("Columns processed", f"{n_cols}"),
            ("Flagged for review", f"{flagged:,}"),
            ("Time elapsed", f"{elapsed:.1f}s"),
            ("Output file", os.path.basename(out_path)),
        ]
        for i, (k, v) in enumerate(rows):
            ctk.CTkLabel(
                body, text=k, font=self._font(11),
                text_color=("gray45", "gray60")
            ).grid(row=i, column=0, sticky="w", pady=3, padx=(0, 16))
            ctk.CTkLabel(
                body, text=str(v), font=self._font(11)
            ).grid(row=i, column=1, sticky="w", pady=3)

        if flagged:
            ctk.CTkLabel(
                dlg, text=f"Review rows where the 'Check {{column}}' is set to Yes.",
                font=self._font(11),
                text_color=("#b35900", "#f0a060"),
                wraplength=380, justify="center"
            ).pack(padx=24, pady=(0, 10))

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=(4, 20))

        ctk.CTkButton(
            btn_row, text="Open File", width=110,
            command=lambda: (self._open_path(out_path), dlg.destroy())
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_row, text="Open Folder", width=110,
            command=lambda: self._open_path(os.path.dirname(out_path))
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_row, text="Close", width=80,
            fg_color="transparent", border_width=1,
            text_color=("gray20", "gray80"),
            hover_color=("gray85", "gray25"),
            command=dlg.destroy
        ).pack(side="left", padx=4)

        dlg.update_idletasks()
        w = dlg.winfo_width() or 460
        h = dlg.winfo_height() or 360
        x = self.winfo_rootx() + max(0, (self.winfo_width() - w) // 2)
        y = self.winfo_rooty() + max(0, (self.winfo_height() - h) // 3)
        dlg.geometry(f"+{x}+{y}")

    def _error(self, msg):
        self.run_btn.configure(state="normal")
        self.progress_bar.set(0)
        self._log("Error. See dialog for details.", "err")
        messagebox.showerror("Error", msg)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = DateFormatterApp()
    app.mainloop()
