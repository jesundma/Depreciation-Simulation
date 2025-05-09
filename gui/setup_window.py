import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db.database_service import DatabaseService
from models.project_model import Project
from gui.status_window import StatusWindow
from gui.window_factory import WindowFactory
import random
import string

def setup_database_window():
    status_window = StatusWindow("Database Setup Status")

    try:
        db_service = DatabaseService()

        status_window.update_status("Creating new tables...")
        db_service.create_tables()

        status_window.update_status("Database setup completed successfully!")
    except Exception as e:
        status_window.update_status(f"Database setup failed:\n{e}")

def setup_depreciation_window():
    """
    Opens the Depreciation Setup window for creating a general depreciation schedule.
    """
    def on_percentage_change(*args):
        if percentage_var.get():
            years_entry.config(state="disabled")
        else:
            years_entry.config(state="normal")

    def on_years_change(*args):
        if years_var.get():
            percentage_entry.config(state="disabled")
        else:
            percentage_entry.config(state="normal")

    def save_depreciation_schedule():
        percentage = percentage_var.get()
        years = years_var.get()
        method_description = method_description_entry.get()

        if not method_description:
            messagebox.showerror("Error", "Please fill in the Method Description field.")
            return

        if not percentage and not years:
            messagebox.showerror("Error", "Please fill either Percentage or Years field.")
            return

        try:
            db_service = DatabaseService()
            db_service.save_depreciation_schedule(
                depreciation_percentage=float(percentage) if percentage else None,
                depreciation_years=int(years) if years else None,
                method_description=method_description
            )
            messagebox.showinfo("Success", "General depreciation schedule saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save depreciation schedule: {e}")

    percentage_var = tk.StringVar()
    percentage_var.trace("w", on_percentage_change)
    years_var = tk.StringVar()
    years_var.trace("w", on_years_change)

    # Use WindowFactory to create the setup window and track widgets
    widget_creators = [
        ("percentage_entry", lambda parent: tk.Entry(parent, textvariable=percentage_var).pack(pady=5)),
        ("years_entry", lambda parent: tk.Entry(parent, textvariable=years_var).pack(pady=5)),
        ("method_description_entry", lambda parent: tk.Entry(parent).pack(pady=5)),
        ("save_button", lambda parent: tk.Button(parent, text="Save", command=save_depreciation_schedule).pack(pady=20)),
        ("close_button", lambda parent: tk.Button(parent, text="Close", command=parent.destroy).pack(pady=5)),
    ]
    window, widgets = WindowFactory.create_generic_window_with_widgets("General Depreciation Setup", "400x300", widget_creators)

    # Access widgets by their keys
    percentage_entry = widgets["percentage_entry"]
    years_entry = widgets["years_entry"]
    method_description_entry = widgets["method_description_entry"]

    window.mainloop()

def show_update_status():
    """
    Displays a window to inform the user that the depreciation schedule description has been updated.
    """
    status_window = tk.Toplevel()
    status_window.title("Update Status")
    status_window.geometry("300x150")

    tk.Label(status_window, text="Depreciation schedule description updated successfully!", font=("Arial", 12), wraplength=250, justify="center").pack(pady=20)

    close_button = ttk.Button(status_window, text="Close", command=status_window.destroy)
    close_button.pack(pady=10)