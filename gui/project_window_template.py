import tkinter as tk
from tkinter import ttk
from services.calculation_service import CalculationService
from services.project_management_service import ProjectManagementService
from constants import year_range
from db.database_service import DatabaseService
from gui.window_factory import WindowFactory

def display_project_window(project):
    """
    Display a project in an independent window using WindowFactory.
    :param project: Dictionary containing project details.
    """
    def create_widgets(parent):
        # Add project details section
        ttk.Label(parent, text="Project Details:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(parent, text="Project ID:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text=project['project_id']).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(parent, text="Branch:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text=project['branch']).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(parent, text="Operations:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text=project['operations']).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(parent, text="Description:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text=project['description'], wraplength=300, justify=tk.LEFT).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)

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
        ttk.Label(parent, text="Depreciation Method:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text=depreciation_description).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

        if investments:
            # Display investment schedule with years as columns
            ttk.Label(parent, text="Investment Schedule:", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=len(investments) + 1, sticky=tk.W, padx=5, pady=5)

            # Add year headers as columns
            ttk.Label(parent, text="Year", font=("Arial", 10, "bold")).grid(row=7, column=0, padx=5, pady=5)
            for idx, investment in enumerate(investments):
                ttk.Label(parent, text=f"{investment['year']}", font=("Arial", 10, "bold")).grid(row=7, column=idx + 1, padx=5, pady=5)

            # Add investment amounts dynamically
            ttk.Label(parent, text="Investment Amount", font=("Arial", 10, "bold")).grid(row=8, column=0, padx=5, pady=5)
            investment_entries = []
            investment_checkboxes = []
            for idx, investment in enumerate(investments):
                entry = ttk.Entry(parent)
                entry.insert(0, str(investment["investment_amount"]))
                entry.grid(row=8, column=idx + 1, padx=5, pady=5)
                investment_entries.append((investment["year"], entry))

                var = tk.BooleanVar(value=bool(investment["depreciation_start_year"]))
                checkbox = ttk.Checkbutton(parent, variable=var)
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

            save_changes_button = ttk.Button(parent, text="Save Changes", command=save_changes)
            save_changes_button.grid(row=11, column=0, columnspan=len(investments) + 1, pady=10)

            # Fetch whether depreciations are calculated for the project
            has_depreciations = db_service.has_calculated_depreciations(project['project_id'])

            # Set button text based on depreciation status
            button_text = "Recalculate Depreciations" if has_depreciations else "No Depreciations Calculated"

            # Add a button to calculate or recalculate depreciation
            calculate_depreciation_button = ttk.Button(
                parent,
                text=button_text,
                command=lambda: CalculationService.handle_depreciation_calculation(project['project_id'])
            )
            calculate_depreciation_button.grid(row=13, column=0, columnspan=len(investments) + 1, pady=10)

            # Add Close button
            close_button = ttk.Button(parent, text="Close", command=parent.winfo_toplevel().destroy)
            close_button.grid(row=12, column=0, columnspan=len(investments) + 1, pady=10)

    # Use WindowFactory to create the project window
    project_window = WindowFactory.create_generic_window_with_widgets(
        title=f"Project: {project['project_id']}",
        geometry="400x400",
        widget_creators=[("details_frame", create_widgets)]
    )

    return project_window