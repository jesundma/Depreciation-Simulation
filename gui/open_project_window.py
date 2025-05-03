import tkinter as tk
from tkinter import ttk
import requests
import os
from services.project_service import ProjectService
from gui.project_window_template import display_project_window
from db.database_service import DatabaseService

FLASK_URL = os.getenv("FLASK_URL", "http://127.0.0.1:5000")

def open_open_project_window(root):
    def close_window():
        popup.destroy()
        root.attributes('-disabled', False)

    def display_results_in_new_window(results):
        # Create a new window for displaying results
        results_window = tk.Toplevel(popup)
        results_window.title("Search Results")

        # Adjust the window size dynamically based on the number of results
        num_rows = len(results)
        window_height = min(400, 50 + num_rows * 30)  # Adjust height dynamically
        results_window.geometry(f"600x{window_height}")

        # Add a canvas and scrollbar for dynamic scrolling
        canvas = tk.Canvas(results_window)
        scrollbar_y = ttk.Scrollbar(results_window, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(results_window, orient=tk.HORIZONTAL, command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Fetch depreciation methods for mapping
        database_service = DatabaseService()
        depreciation_methods = database_service.fetch_depreciation_methods()

        # Add a new column header for Depreciation Method
        headers = ["", "Project ID", "Branch", "Operations", "Description", "Depreciation Method"]
        for col, header in enumerate(headers):
            ttk.Label(scrollable_frame, text=header, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5)

        # Display rows of results with depreciation method descriptions
        if not results:
            ttk.Label(scrollable_frame, text="No results found.", font=("Arial", 10, "italic"), foreground="red").grid(row=1, column=0, columnspan=len(headers) + 2, pady=10)
        else:
            checkboxes = []

            for row, project in enumerate(results, start=1):
                var = tk.BooleanVar()
                checkbox = ttk.Checkbutton(scrollable_frame, variable=var)
                checkbox.grid(row=row, column=0, padx=5, pady=5)
                checkboxes.append((var, project))

                ttk.Label(scrollable_frame, text=project['project_id']).grid(row=row, column=1, padx=5, pady=5)
                ttk.Label(scrollable_frame, text=project['branch']).grid(row=row, column=2, padx=5, pady=5)
                ttk.Label(scrollable_frame, text=project['operations']).grid(row=row, column=3, padx=5, pady=5)
                ttk.Label(scrollable_frame, text=project['description']).grid(row=row, column=4, padx=5, pady=5)

                # Map and display the depreciation method description
                depreciation_description = depreciation_methods.get(project['depreciation_method'], "Unknown")
                ttk.Label(scrollable_frame, text=depreciation_description).grid(row=row, column=5, padx=5, pady=5)

            def open_selected_projects():
                selected_projects = [project for var, project in checkboxes if var.get()]
                if selected_projects:
                    for project in selected_projects:
                        print(f"Calling display_project_window with project: {project}")
                        display_project_window(project)
                else:
                    print("No projects selected.")

            open_button = ttk.Button(results_window, text="Open Selected", command=open_selected_projects)
            open_button.pack(pady=10)

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
                results = ProjectService.search_projects(
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