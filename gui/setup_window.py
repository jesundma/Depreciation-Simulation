import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db.database_service import DatabaseService
from models.project_model import Project
import random
import string

def setup_database():
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
    Opens the Depreciation Setup window.
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
        project_id = project_id_entry.get()
        schedule = schedule_entry.get()
        percentage = percentage_var.get()
        years = years_var.get()
        method_description = method_description_entry.get()

        if not project_id or not schedule or not method_description:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        if not percentage and not years:
            messagebox.showerror("Error", "Please fill either Percentage or Years field.")
            return

        messagebox.showinfo("Success", "Depreciation schedule saved successfully.")

    window = tk.Toplevel()
    window.title("Depreciation Setup")
    window.geometry("400x400")

    tk.Label(window, text="Project ID:").pack(pady=5)
    project_id_entry = tk.Entry(window)
    project_id_entry.pack(pady=5)

    tk.Label(window, text="Schedule:").pack(pady=5)
    schedule_entry = tk.Entry(window)
    schedule_entry.pack(pady=5)

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

def setup_test_database():
    """
    Opens a window to display the status of setting up a test database.
    """
    status_window = tk.Toplevel()
    status_window.title("Setup Test Database")
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

    db_service = DatabaseService()

    def random_string(length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    try:
        update_status("Creating 6 entries for Setup Test Database...")
        for i in range(1, 7):
            project_id = random_string(6)
            branch = random_string(5)
            operations = random_string(5)
            description = random_string(5)

            # Create a Project instance
            project = Project(
                project_id=project_id,
                branch=branch,
                operations=operations,
                description=description
            )

            # Save the project to the database
            db_service.save_project(project)

            update_status(f"Entry {i} created successfully with Project ID: {project_id}, Branch: {branch}, Operations: {operations}, Description: {description}.")

        update_status("Setup Test Database completed successfully!")

    except Exception as e:
        update_status(f"Setup Test Database failed:\n{e}")

    close_button = ttk.Button(status_window, text="Close", command=status_window.destroy)
    close_button.pack(pady=20)