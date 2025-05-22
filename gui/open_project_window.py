import tkinter as tk
from tkinter import ttk
import requests
import os
from services.project_management_service import ProjectManagementService
from gui.project_window_template import display_project_window
from db.database_service import DatabaseService
from gui.window_factory import WindowFactory

FLASK_URL = os.getenv("FLASK_URL", "http://127.0.0.1:5000")

def open_open_project_window(root):
    def close_window():
        popup.destroy()
        root.attributes('-disabled', False)

    def display_results_in_new_window(results):
        # Map depreciation method IDs to their descriptions
        db_service = DatabaseService()
        depreciation_methods = db_service.fetch_depreciation_methods()
        for result in results:
            result['depreciation_method'] = depreciation_methods.get(result['depreciation_method'], 'Unknown')

        results_window = WindowFactory.create_generic_window(
            title="Search Results",
            geometry="600x400",
            widgets=[
                lambda parent: ttk.Label(parent, text="Search Results", font=("Arial", 14)).pack(pady=10),
                lambda parent: ttk.Treeview(parent, columns=("Column1", "Column2"), show="headings").pack(expand=True, fill="both")
            ]
        )
        
        # Populate the Treeview with search results
        treeview = results_window.children['!treeview']  # Assuming the Treeview is the only one in the window
        treeview['columns'] = list(results[0].keys())  # Set columns based on result keys
        for col in treeview['columns']:
            treeview.heading(col, text=col)
            treeview.column(col, width=100, anchor='center')
        for result in results:
            treeview.insert('', 'end', values=list(result.values()))
        
        # Add double-click functionality to open a project
        def on_project_select(event):
            selected_item = treeview.selection()
            if selected_item:
                project_data = treeview.item(selected_item, 'values')
                project_dict = {key: value for key, value in zip(treeview['columns'], project_data)}
                display_project_window(project_dict)

        treeview.bind('<Double-1>', on_project_select)
        
        return results_window

    def is_server_running():
        return False  # Default to desktop database connection if Flask is not running

    def search_project():
        project_id = entry_project_id.get()
        branch = entry_branch.get()
        operations = entry_operations.get()
        description = text_field.get("1.0", tk.END).strip()

        if is_server_running():
            # Call backend API to search for projects
            params = {
                "project_id": project_id,
                "branch": branch,
                "operations": operations,
                "description": description
            }
            try:
                response = requests.get(f"{FLASK_URL}/api/projects/search", params=params)
                if response.status_code == 200:
                    results = response.json()
                    display_results_in_new_window(results)
                else:
                    print(f"Error: {response.json().get('error', 'Unknown error')}")
            except Exception as e:
                print(f"Error connecting to server: {e}")
        else:
            # Fallback to local database access
            try:
                results = ProjectManagementService.search_projects(
                    project_id=project_id,
                    branch=branch,
                    operations=operations,
                    description=description
                )
                display_results_in_new_window(results)
            except Exception as e:
                print(f"Error accessing local database: {e}")

    root.attributes('-disabled', True)
    popup = tk.Toplevel(root)
    popup.title("Open Project")
    popup.geometry("600x500")  # Increased window size to fit all elements

    # Adjust padding for better layout
    ttk.Label(popup, text="Project ID:").pack(pady=(10, 5))
    entry_project_id = ttk.Entry(popup)
    entry_project_id.pack(pady=(0, 10))

    ttk.Label(popup, text="Branch:").pack(pady=(10, 5))
    entry_branch = ttk.Entry(popup)
    entry_branch.pack(pady=(0, 10))

    ttk.Label(popup, text="Operations:").pack(pady=(10, 5))
    entry_operations = ttk.Entry(popup)
    entry_operations.pack(pady=(0, 10))

    ttk.Label(popup, text="Description:").pack(pady=(10, 5))
    text_field = tk.Text(popup, height=5, width=40)
    text_field.pack(pady=(0, 10))

    # Fetch depreciation methods for the dropdown
    database_service = DatabaseService()
    depreciation_methods = database_service.fetch_depreciation_methods()

    # Update dropdown to show descriptions
    ttk.Label(popup, text="Depreciation Method:").pack(pady=(10, 5))
    depreciation_method_var = tk.StringVar()
    depreciation_method_dropdown = ttk.Combobox(
        popup, 
        textvariable=depreciation_method_var, 
        values=list(depreciation_methods.values()),  # Show descriptions in the dropdown
        state="readonly"
    )
    depreciation_method_dropdown.pack(pady=(0, 10))

    search_button = ttk.Button(popup, text="Search", command=search_project)
    search_button.pack(pady=(20, 10))

    # Add a frame to display search results
    results_frame = ttk.Frame(popup)
    results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

    popup.protocol("WM_DELETE_WINDOW", close_window)