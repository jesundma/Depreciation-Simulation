import tkinter as tk
from tkinter import filedialog, messagebox
from gui.status_window import StatusWindow
from services.import_service import ImportService

def create_investments_from_dataframe_gui():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(
        title="Select Excel File for Investments Import",
        filetypes=[("Excel Files", "*.xlsx *.xls")]
    )
    if not file_path:
        return

    status_window = StatusWindow("Import Investments Status")

    def status_callback(message):
        status_window.update_status(message)

    try:
        ImportService.create_investments_from_dataframe(file_path, status_callback=status_callback)
        status_window.update_status("[SUCCESS] Investments import completed.")
    except Exception as e:
        status_window.update_status(f"[ERROR] {str(e)}")
        messagebox.showerror("Import Error", str(e))

    status_window.wait_window()  # Wait until the status window is closed
