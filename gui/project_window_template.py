import tkinter as tk
from tkinter import ttk
from services.calculation_service import CalculationService
from services.project_management_service import ProjectManagementService
from constants import year_range
from db.database_service import DatabaseService
from gui.window_factory import WindowFactory

def fetch_investment_schedule(project_id):
    """Fetch and prepare the investment schedule for a project."""
    db_service = DatabaseService()
    investments = db_service.get_investment_schedule(project_id)

    # Handle cases where investments might be None
    if not investments:
        investments = []

    # Debug: Print investments data to inspect structure
    print("[DEBUG] Investments data:", investments)

    # Process investments by year, allowing multiple investments per year
    investments_dict = {}
    for investment in investments:
        if isinstance(investment, dict):
            year = investment.get("year", 0)
            if year not in investments_dict:
                investments_dict[year] = {
                    "year": year,
                    "investment_amount": 0.0,
                    "start_year": investment.get("start_year")
                }
            # Accumulate investment amounts for the same year
            investments_dict[year]["investment_amount"] += float(investment.get("investment_amount", 0.0))

    # Ensure years up to the maximum in year_range are included
    min_year, max_year = year_range[0], year_range[-1]
    investments = []
    for year in range(min_year, max_year + 1):
        if year in investments_dict:
            investments.append(investments_dict[year])
        else:
            investments.append({"year": year, "investment_amount": 0.0, "start_year": None})

    return investments

def create_investment_widgets(parent, investments):
    """Create widgets for displaying and editing the investment schedule."""
    # Ensure investments is a valid list
    if not investments or not isinstance(investments, list):
        investments = []

    # Debug: Trace the source of investments
    print("[DEBUG] Received investments:", investments)

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

        var = tk.BooleanVar(value=bool(investment.get("start_year", False)))
        checkbox = ttk.Checkbutton(parent, variable=var)
        checkbox.grid(row=9, column=idx + 1, padx=5, pady=5)
        investment_checkboxes.append((investment["year"], var))

    # Add a new row of boxes for depreciation months
    ttk.Label(parent, text="Depreciation Month", font=("Arial", 10, "bold")).grid(row=10, column=0, padx=5, pady=5)
    depreciation_month_entries = []
    for idx, investment in enumerate(investments):
        month_entry = ttk.Entry(parent, width=5)  # Set width to half the current size
        month_entry.insert(0, "")  # Default empty value
        month_entry.grid(row=10, column=idx + 1, padx=5, pady=5)
        depreciation_month_entries.append((investment["year"], month_entry))

    # Add a title for tick marks
    ttk.Label(parent, text="Depreciation Years", font=("Arial", 10, "bold")).grid(row=9, column=0, padx=5, pady=5)

    return investment_entries, investment_checkboxes, depreciation_month_entries

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

        # Query investment schedule using helper function
        if not project.get('project_id'):
            return

        investments = fetch_investment_schedule(project['project_id'])

        # Fetch the depreciation method description
        db_service = DatabaseService()
        depreciation_methods = db_service.fetch_depreciation_methods()
        depreciation_description = depreciation_methods.get(project['depreciation_method'], "Unknown")

        # Add depreciation method description to the project details
        ttk.Label(parent, text="Depreciation Method:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text=depreciation_description).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

        if investments:
            # Create investment widgets using helper function
            investment_entries, investment_checkboxes, depreciation_month_entries = create_investment_widgets(parent, investments)

            def save_changes():
                updated_investments = {}
                for (year, entry), (_, var), (_, month_entry) in zip(investment_entries, investment_checkboxes, depreciation_month_entries):
                    try:
                        investment_amount = float(entry.get())
                        start_year = year if var.get() else None
                        start_month = int(month_entry.get()) if month_entry.get().isdigit() else None
                        updated_investments[year] = (investment_amount, start_year, start_month)
                    except ValueError:
                        updated_investments[year] = (0.0, None, None)

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