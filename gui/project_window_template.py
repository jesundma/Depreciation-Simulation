import tkinter as tk
from tkinter import ttk
from services.project_service import DatabaseService
from db.database_service import DatabaseService
from services.project_service import ProjectService

def display_project_window(project):
    """
    Display a project in an independent window.
    :param project: Dictionary containing project details.
    """
    print("display_project_window function called")
    project_window = tk.Toplevel()
    project_window.title(f"Project: {project['project_id']}")
    project_window.geometry("400x400")

    # Configure the project window to dynamically adjust with content
    project_window.columnconfigure(0, weight=1)
    project_window.rowconfigure(0, weight=1)

    # Add a scrollbar to the project window
    scrollbar = ttk.Scrollbar(project_window, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the details frame to work with the scrollbar
    canvas = tk.Canvas(project_window, yscrollcommand=scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=canvas.yview)

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
    print(f"Initializing DatabaseService...")
    db_service = DatabaseService()

    if not project.get('project_id'):
        print("Error: Project ID is missing or None.")
        return

    print(f"Fetching investment schedule for project ID: {project['project_id']}")
    print(f"Project ID passed to get_investment_schedule: {project['project_id']}")
    investments = db_service.get_investment_schedule(project['project_id'])
    print(f"Investment schedule query executed. Results: {investments}")
    print(f"Query results for project ID {project['project_id']}: {investments}")

    # Fetch the depreciation method description
    depreciation_methods = db_service.fetch_depreciation_methods()
    depreciation_description = depreciation_methods.get(project['depreciation_method'], "Unknown")

    # Add depreciation method description to the project details
    ttk.Label(details_frame, text="Depreciation Method:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=depreciation_description).grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)

    if investments:
        print("Displaying investment schedule...")
        # Display investment schedule with years as columns
        ttk.Label(details_frame, text="Investment Schedule:", font=("Arial", 10, "bold")).grid(row=6, column=0, columnspan=len(investments) + 1, sticky=tk.W, padx=5, pady=5)

        # Add year headers as columns
        ttk.Label(details_frame, text="Year", font=("Arial", 10, "bold")).grid(row=7, column=0, padx=5, pady=5)
        for idx, investment in enumerate(investments):
            ttk.Label(details_frame, text=f"{investment['year']}", font=("Arial", 10, "bold")).grid(row=7, column=idx + 1, padx=5, pady=5)

        # Fetch depreciation start years from the database
        depreciation_start_years = {investment['year']: investment['depreciation_start_year'] for investment in investments}

        # Add investment amounts as a single row with checkboxes
        ttk.Label(details_frame, text="Investment Amount", font=("Arial", 10, "bold")).grid(row=8, column=0, padx=5, pady=5)
        investment_entries = []
        for idx, investment in enumerate(investments):
            entry = ttk.Entry(details_frame)
            entry.insert(0, str(investment['investment_amount']))
            entry.grid(row=8, column=idx + 1, padx=5, pady=5)

            # Add a checkbox for each investment and tick it if the year is not null
            var = tk.BooleanVar(value=bool(depreciation_start_years.get(investment['year'])))
            checkbox = ttk.Checkbutton(details_frame, variable=var)
            checkbox.grid(row=9, column=idx + 1, padx=5, pady=5)

            investment_entries.append((investment['year'], entry, var))

        def save_changes():
            updated_investments = {}
            for year, entry, var in investment_entries:
                try:
                    updated_investments[year] = (float(entry.get()), year if var.get() else None)
                except ValueError:
                    updated_investments[year] = (0.0, None)

            print(f"Saving updated investments for project ID {project['project_id']}: {updated_investments}")
            db_service.save_investment_details(project['project_id'], updated_investments)
            print("Investments and depreciation start years updated successfully.")

        save_changes_button = ttk.Button(details_frame, text="Save Changes", command=save_changes)
        save_changes_button.grid(row=10, column=0, columnspan=len(investments) + 1, pady=10)

        # Add a Close button next to the Save Changes button
        close_button = ttk.Button(details_frame, text="Close", command=project_window.destroy)
        close_button.grid(row=11, column=0, columnspan=len(investments) + 1, pady=10, padx=5)

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
        calculate_depreciation_button.grid(row=12, column=0, columnspan=2, pady=10)
    else:
        print("No investment schedule found.")
        # Clear any previous content in the details_frame
        for widget in details_frame.winfo_children():
            widget.destroy()

        def open_investment_year_window():
            # Create a new window to request the start year for investments
            year_window = tk.Toplevel(project_window)
            year_window.title("Enter Start and End Year")
            year_window.geometry("300x200")

            ttk.Label(year_window, text="Enter Start Year:", font=("Arial", 10, "bold")).pack(pady=10)
            year_entry = ttk.Entry(year_window)
            year_entry.pack(pady=5)

            ttk.Label(year_window, text="Enter End Year:", font=("Arial", 10, "bold")).pack(pady=10)
            end_year_entry = ttk.Entry(year_window)
            end_year_entry.pack(pady=5)

            # Fetch depreciation methods for the dropdown
            database_service = DatabaseService()
            depreciation_methods = database_service.fetch_depreciation_methods()

            # Update dropdown to show descriptions
            ttk.Label(year_window, text="Select Depreciation Method:", font=("Arial", 10, "bold")).pack(pady=10)
            depreciation_method_var = tk.StringVar()
            depreciation_method_dropdown = ttk.Combobox(
                year_window, 
                textvariable=depreciation_method_var, 
                values=list(depreciation_methods.values()),  # Show descriptions in the dropdown
                state="readonly"
            )
            depreciation_method_dropdown.pack(pady=5)

            def open_yearly_fields_window():
                try:
                    start_year = int(year_entry.get())
                    end_year = int(end_year_entry.get())

                    if end_year < start_year:
                        raise ValueError("End year must be greater than or equal to start year.")

                    year_window.destroy()

                    # Create a new window for yearly investment fields
                    yearly_window = tk.Toplevel(project_window)
                    yearly_window.title("Yearly Investments")
                    yearly_window.geometry("400x400")

                    ttk.Label(yearly_window, text="Enter Yearly Investments", font=("Arial", 12, "bold")).pack(pady=10)

                    yearly_frame = ttk.Frame(yearly_window)
                    yearly_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                    year_fields = []
                    for year in range(start_year, end_year + 1):
                        ttk.Label(yearly_frame, text=f"Year {year}:", font=("Arial", 10)).grid(row=year - start_year, column=0, padx=5, pady=5)
                        entry = ttk.Entry(yearly_frame)
                        entry.grid(row=year - start_year, column=1, padx=5, pady=5)

                        # Add a checkbox for each year
                        var = tk.BooleanVar()
                        checkbox = ttk.Checkbutton(yearly_frame, variable=var)
                        checkbox.grid(row=year - start_year, column=2, padx=5, pady=5)

                        year_fields.append((year, entry, var))

                    def save_investments():
                        investments = {}
                        for year, entry, var in year_fields:
                            try:
                                investments[year] = (float(entry.get()), year if var.get() else None)
                            except ValueError:
                                investments[year] = (0.0, None)

                        print(f"Saving investments for project ID {project['project_id']}: {investments}")
                        db_service.save_investments(project['project_id'], investments)
                        yearly_window.destroy()
                        print("Investments saved successfully.")

                    # Ensure the Save Investments button is properly packed
                    save_button = ttk.Button(yearly_window, text="Save Investments", command=save_investments)
                    save_button.pack(pady=10, side=tk.BOTTOM, anchor=tk.S)

                except ValueError as e:
                    ttk.Label(year_window, text=str(e), foreground="red").pack()

            submit_button = ttk.Button(year_window, text="Submit", command=open_yearly_fields_window)
            submit_button.pack(pady=10)

        # Update the no investment button to open the new window
        no_investment_button = ttk.Button(details_frame, text="Add Investment Schedule", command=open_investment_year_window)
        no_investment_button.grid(row=0, column=0, columnspan=2, pady=10)

        # Add a Close button for closing the window without changes
        close_button = ttk.Button(details_frame, text="Close", command=project_window.destroy)
        close_button.grid(row=1, column=0, columnspan=2, pady=10)