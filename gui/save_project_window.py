import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from models.project_model import Project
from services.project_management_service import ProjectManagementService
from db.database_service import DatabaseService

def open_save_project_window(root):
    def save_data():
        project_id = entry_project_id.get()
        branch = entry_branch.get()
        operations = entry_operations.get()
        description = text_field.get("1.0", tk.END).strip()
        selected_description = depreciation_method_var.get()

        # Map the selected description to its corresponding key
        depreciation_method_key = next((key for key, desc in depreciation_methods.items() if desc == selected_description), None)

        if not project_id or not branch or not operations or not description or not depreciation_method_key:
            messagebox.showerror("Input Error", "All fields must be filled.")
            return

        project = Project(
            project_id=project_id,
            branch=branch,
            operations=operations,
            description=description,
            depreciation_method=depreciation_method_key
        )

        try:
            ProjectManagementService.save_to_database(project)
            messagebox.showinfo("Data Saved", "Your project has been saved successfully.")
            close_window()
        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred: {e}")

    def close_window():
        popup.destroy()
        root.attributes('-disabled', False)

    root.attributes('-disabled', True)
    popup = tk.Toplevel(root)
    popup.title("Create Project")
    popup.geometry("500x400")

    ttk.Label(popup, text="Project ID:").pack(pady=(10, 0))
    entry_project_id = ttk.Entry(popup)
    entry_project_id.pack()

    ttk.Label(popup, text="Branch:").pack(pady=(10, 0))
    entry_branch = ttk.Entry(popup)
    entry_branch.pack()

    ttk.Label(popup, text="Operations:").pack(pady=(10, 0))
    entry_operations = ttk.Entry(popup)
    entry_operations.pack()

    ttk.Label(popup, text="Description:").pack(pady=(10, 0))
    text_field = tk.Text(popup, height=5, width=30)
    text_field.pack()

    database_service = DatabaseService()
    depreciation_methods = database_service.fetch_depreciation_methods()

    ttk.Label(popup, text="Depreciation Method:").pack(pady=(10, 0))
    depreciation_method_var = tk.StringVar()
    depreciation_method_dropdown = ttk.Combobox(
        popup, 
        textvariable=depreciation_method_var, 
        values=list(depreciation_methods.values()),  # Show descriptions in the dropdown
        state="readonly"
    )
    depreciation_method_dropdown.pack()

    save_button = ttk.Button(popup, text="Create", command=save_data)
    save_button.pack(pady=20)

    popup.protocol("WM_DELETE_WINDOW", close_window)