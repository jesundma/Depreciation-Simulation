from gui.status_window import StatusWindow
import tkinter as tk
from services.import_service import ImportService

def create_depreciation_starts_from_dataframe_gui():
    """
    Desktop GUI handler for importing depreciation starts from Excel with confirmation dialog and status window.
    Shows a warning that obsolete depreciation starts and associated data will be deleted, and asks for confirmation.
    """
    def proceed_with_import():
        status_window.window.destroy()  # Close the warning window
        status = StatusWindow("Import Depreciation Starts Status")
        def status_callback(message):
            status.update_status(message)
        try:
            ImportService.create_depreciation_starts_from_dataframe(status_callback=status_callback)
            status.update_status("[INFO] Depreciation starts have been successfully imported and saved to the database.")
        except Exception as e:
            status.update_status(f"[ERROR] {str(e)}")
        status.window.grab_set()
        status.window.wait_window()

    def cancel_import():
        status_window.window.destroy()
        print("[INFO] Depreciation starts import cancelled by user.")

    # Show warning window
    status_window = StatusWindow("Warning: Import Depreciation Starts")
    status_window.update_status(
        "[WARNING] Importing depreciation starts may delete obsolete depreciation start data.\n\nDo you want to continue?"
    )
    # Add YES/NO buttons
    yes_button = tk.Button(status_window.window, text="YES", command=proceed_with_import, width=10, bg="red", fg="white")
    yes_button.pack(pady=(10, 5))
    no_button = tk.Button(status_window.window, text="NO", command=cancel_import, width=10)
    no_button.pack(pady=(0, 10))
    # Prevent further execution until user responds
    status_window.window.grab_set()
    status_window.window.wait_window()
