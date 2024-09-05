import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
from datetime import datetime

# Initialize Tkinter
root = tk.Tk()
root.withdraw()  # Hide the main window

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

# Function to prompt the user to select a column from a dropdown list
def select_column(df):
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

# Function to fix date discrepancies
def fix_date_range(date_range):
    try:
        # Split the date range into start and end
        start_date_str, end_date_str = date_range.split(" - ")

        # Convert the dates to datetime objects
        start_date = datetime.strptime(start_date_str.strip(), '%m/%d/%Y')
        end_date = datetime.strptime(end_date_str.strip(), '%m/%d/%Y')

        # Ensure the dates are in the correct order
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        # Format the dates back to MM/DD/YYYY
        fixed_date_range = f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        return fixed_date_range
    except ValueError:
        # If the date parsing fails, return the original string
        return date_range

# Select the file
file_path = select_file()

# Determine the file extension and load the file accordingly
if file_path.endswith('.csv'):
    df = pd.read_csv(file_path)
else:
    df = pd.read_excel(file_path)

# Prompt the user to select the column to format
select_column(df)

# Check if the specified column exists
if column_to_format not in df.columns:
    messagebox.showerror("Error", f"The column '{column_to_format}' does not exist in the file.")
    root.destroy()
    exit()

# Apply the fix to the selected column
df['CleanedOutput'] = df[column_to_format].apply(fix_date_range)

# Save the cleaned DataFrame back to a new file
output_file_path = file_path.replace('.csv', '_cleaned.csv').replace('.xlsx', '_cleaned.xlsx')

if file_path.endswith('.csv'):
    df.to_csv(output_file_path, index=False)
else:
    df.to_excel(output_file_path, index=False)

# Show completion message
messagebox.showinfo("Completion", f"Cleaned data saved to {output_file_path}")
root.destroy()
