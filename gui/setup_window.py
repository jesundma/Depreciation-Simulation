import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db.database_service import DatabaseService
from models.project_model import Project
import random
import string

def setup_database_window():
    """
    Sets up the database by clearing all tables and creating new ones.
    """
    status_window = tk.Toplevel()
    status_window.title("Database Setup Status")
    status_window.geometry("400x300")

    text_area = tk.Text(status_window, wrap=tk.WORD, font=("Arial", 12), height=15, width=50)
    text_area.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(status_window, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.config(yscrollcommand=scrollbar.set)

    def update_status(message):
        text_area.insert(tk.END, message + "\n")
        text_area.see(tk.END)
        status_window.update_idletasks()

    try:
        db_service = DatabaseService()

        update_status("Clearing all tables...")
        db_service.clear_all_tables()

        update_status("Creating new tables...")
        db_service.create_tables()

        update_status("Database setup completed successfully!")

    except Exception as e:
        update_status(f"Database setup failed:\n{e}")

    close_button = ttk.Button(status_window, text="Close", command=status_window.destroy)
    close_button.pack(pady=20)

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

    window = tk.Toplevel()
    window.title("General Depreciation Setup")
    window.geometry("400x300")

    tk.Label(window, text="Depreciation Percentage:").pack(pady=5)
    percentage_var = tk.StringVar()
    percentage_var.trace("w", on_percentage_change)
    percentage_entry = tk.Entry(window, textvariable=percentage_var)
    percentage_entry.pack(pady=5)

    tk.Label(window, text="Depreciation Years:").pack(pady=5)
    years_var = tk.StringVar()
    years_var.trace("w", on_years_change)
    years_entry = tk.Entry(window, textvariable=years_var)
    years_entry.pack(pady=5)

    tk.Label(window, text="Method Description:").pack(pady=5)
    method_description_entry = tk.Entry(window)
    method_description_entry.pack(pady=5)

    save_button = tk.Button(window, text="Save", command=save_depreciation_schedule)
    save_button.pack(pady=20)

    close_button = tk.Button(window, text="Close", command=window.destroy)
    close_button.pack(pady=5)

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