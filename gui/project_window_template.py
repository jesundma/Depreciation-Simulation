import tkinter as tk
from tkinter import ttk
from services.project_service import DatabaseService
from db.database_service import DatabaseService
from services.project_service import ProjectService
from constants import year_range

def display_project_window(project):
    """
    Display a project in an independent window.
    :param project: Dictionary containing project details.
    """
    project_window = tk.Toplevel()
    project_window.title(f"Project: {project['project_id']}")
    project_window.geometry("400x400")

    # Configure the project window to dynamically adjust with content
    project_window.columnconfigure(0, weight=1)
    project_window.rowconfigure(0, weight=1)

    # Add a scrollbar to the project window
    scrollbar = ttk.Scrollbar(project_window, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Add a horizontal scrollbar to the project window
    h_scrollbar = ttk.Scrollbar(project_window, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Configure the canvas to work with both scrollbars
    canvas = tk.Canvas(project_window, yscrollcommand=scrollbar.set, xscrollcommand=h_scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=canvas.yview)
    h_scrollbar.config(command=canvas.xview)

    # Create a frame inside the canvas
    details_frame = ttk.Frame(canvas)

    # Add the frame to the canvas
    canvas.create_window((0, 0), window=details_frame, anchor="nw")

    # Configure the canvas to resize with the window
    details_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Display project details
    ttk.Label(project_window, text="Project Details", font=("Arial", 14, "bold")).pack(pady=10)

    # Configure the details frame to expand with content
    details_frame.columnconfigure(1, weight=1)
    details_frame.rowconfigure(0, weight=1)

    # Add project details section
    ttk.Label(details_frame, text="Project Details:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

    ttk.Label(details_frame, text="Project ID:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['project_id']).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

    ttk.Label(details_frame, text="Branch:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['branch']).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

    ttk.Label(details_frame, text="Operations:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['operations']).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

    ttk.Label(details_frame, text="Description:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['description'], wraplength=300, justify=tk.LEFT).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

    # Query investment schedule using DatabaseService
    db_service = DatabaseService()

    if not project.get('project_id'):
        return

    investments = db_service.get_investment_schedule(project['project_id'])

    # Ensure years up to the maximum in year_range are included
    min_year, max_year = year_range[0], year_range[-1]
    investments_dict = {investment["year"]: investment for investment in investments}
    investments = []
    for year in range(min_year, max_year + 1):
        if year in investments_dict:
            investments.append(investments_dict[year])
        else:
            investments.append({"year": year, "investment_amount": 0.0, "depreciation_start_year": None})

    # Fetch the depreciation method description
    depreciation_methods = db_service.fetch_depreciation_methods()
    depreciation_description = depreciation_methods.get(project['depreciation_method'], "Unknown")

    # Add depreciation method description to the project details
    ttk.Label(details_frame, text="Depreciation Method:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=depreciation_description).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

    if investments:
        # Display investment schedule with years as columns
        ttk.Label(details_frame, text="Investment Schedule:", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=len(investments) + 1, sticky=tk.W, padx=5, pady=5)

        # Add year headers as columns
        ttk.Label(details_frame, text="Year", font=("Arial", 10, "bold")).grid(row=7, column=0, padx=5, pady=5)
        for idx, investment in enumerate(investments):
            ttk.Label(details_frame, text=f"{investment['year']}", font=("Arial", 10, "bold")).grid(row=7, column=idx + 1, padx=5, pady=5)

        # Add investment amounts dynamically
        ttk.Label(details_frame, text="Investment Amount", font=("Arial", 10, "bold")).grid(row=8, column=0, padx=5, pady=5)
        investment_entries = []
        investment_checkboxes = []
        for idx, investment in enumerate(investments):
            entry = ttk.Entry(details_frame)
            entry.insert(0, str(investment["investment_amount"]))
            entry.grid(row=8, column=idx + 1, padx=5, pady=5)
            investment_entries.append((investment["year"], entry))

            var = tk.BooleanVar(value=bool(investment["depreciation_start_year"]))
            checkbox = ttk.Checkbutton(details_frame, variable=var)
            checkbox.grid(row=9, column=idx + 1, padx=5, pady=5)
            investment_checkboxes.append((investment["year"], var))

        def save_changes():
            updated_investments = {}
            for (year, entry), (_, var) in zip(investment_entries, investment_checkboxes):
                try:
                    updated_investments[year] = (float(entry.get()), year if var.get() else None)
                except ValueError:
                    updated_investments[year] = (0.0, None)

            db_service.save_investment_details(project['project_id'], updated_investments)

        save_changes_button = ttk.Button(details_frame, text="Save Changes", command=save_changes)
        save_changes_button.grid(row=11, column=0, columnspan=len(investments) + 1, pady=10)

        # Fetch whether depreciations are calculated for the project
        has_depreciations = db_service.has_calculated_depreciations(project['project_id'])

        # Set button text based on depreciation status
        button_text = "Recalculate Depreciations" if has_depreciations else "No Depreciations Calculated"

        # Add a button to calculate or recalculate depreciation
        calculate_depreciation_button = ttk.Button(
            details_frame,
            text=button_text,
            command=lambda: ProjectService.handle_depreciation_calculation(project['project_id'])
        )
        calculate_depreciation_button.grid(row=13, column=0, columnspan=len(investments) + 1, pady=10)

        # Add Close button
        close_button = ttk.Button(details_frame, text="Close", command=project_window.destroy)
        close_button.grid(row=12, column=0, columnspan=len(investments) + 1, pady=10)