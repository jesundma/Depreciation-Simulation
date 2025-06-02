from gui.status_window import StatusWindow
import tkinter as tk
from services.import_service import ImportService

def create_projects_from_dataframe_gui():
    """
    Desktop GUI handler for importing projects from Excel with confirmation dialog.
    Shows a warning that obsolete projects and associated data will be deleted, and asks for confirmation.
    """
    def proceed_with_import():
        status_window.window.destroy()  # Close the warning window
        df = ImportService.read_excel_to_dataframe(
            title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if df is None:
            return
        ImportService.create_projects_from_dataframe(df=df)
        print("[INFO] Projects have been successfully imported and saved to the database.")

    def cancel_import():
        status_window.window.destroy()
        print("[INFO] Project import cancelled by user.")

    # Show warning window
    status_window = StatusWindow("Warning: Import Projects")
    status_window.update_status(
        "[WARNING] Importing projects will delete all obsolete projects and all data associated with them (including investments, classifications, etc.).\n\nDo you want to continue?"
    )
    # Add YES/NO buttons
    yes_button = tk.Button(status_window.window, text="YES", command=proceed_with_import, width=10, bg="red", fg="white")
    yes_button.pack(pady=(10, 5))
    no_button = tk.Button(status_window.window, text="NO", command=cancel_import, width=10)
    no_button.pack(pady=(0, 10))
    # Prevent further execution until user responds
    status_window.window.grab_set()
    status_window.window.wait_window()
