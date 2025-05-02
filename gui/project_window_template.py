import tkinter as tk
from tkinter import ttk
from services.project_service import DatabaseService

def display_project_window(project):
    """
    Display a project in an independent window.
    :param project: Dictionary containing project details.
    """
    print("display_project_window function called")
    project_window = tk.Toplevel()
    project_window.title(f"Project: {project['project_id']}")
    project_window.geometry("400x400")

    # Display project details
    ttk.Label(project_window, text="Project Details", font=("Arial", 14, "bold")).pack(pady=10)

    details_frame = ttk.Frame(project_window)
    details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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

    if investments:
        print("Displaying investment schedule...")
        ttk.Label(details_frame, text="Investment Schedule:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)

        investment_entries = []
        for idx, investment in enumerate(investments, start=6):
            ttk.Label(details_frame, text=f"Year {investment['year']}:", font=("Arial", 10)).grid(row=idx, column=0, sticky=tk.W, padx=5, pady=5)
            entry = ttk.Entry(details_frame)
            entry.insert(0, str(investment['investment_amount']))
            entry.grid(row=idx, column=1, sticky=tk.W, padx=5, pady=5)
            investment_entries.append((investment['year'], entry))

        def show_changes_saved_window():
            """Display a window indicating changes were saved successfully."""
            saved_window = tk.Toplevel(project_window)
            saved_window.title("Changes Saved")
            saved_window.geometry("300x150")

            ttk.Label(saved_window, text="Changes saved successfully!", font=("Arial", 12, "bold")).pack(pady=20)

            close_button = ttk.Button(saved_window, text="Close", command=saved_window.destroy)
            close_button.pack(pady=10)

        def save_changes():
            updated_investments = {}
            for year, entry in investment_entries:
                try:
                    updated_investments[year] = float(entry.get())
                except ValueError:
                    updated_investments[year] = 0.0

            print(f"Saving updated investments for project ID {project['project_id']}: {updated_investments}")
            db_service.save_investments(project['project_id'], updated_investments)
            print("Investments updated successfully.")

            # Show the changes saved window
            show_changes_saved_window()

        save_changes_button = ttk.Button(details_frame, text="Save Changes", command=save_changes)
        save_changes_button.grid(row=len(investments) + 6, column=0, columnspan=2, pady=10)

        # Add a Close button next to the Save Changes button
        close_button = ttk.Button(details_frame, text="Close", command=project_window.destroy)
        close_button.grid(row=len(investments) + 6, column=2, pady=10, padx=5)
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
                                investments[year] = float(entry.get())
                            except ValueError:
                                investments[year] = 0.0

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
        no_investment_button = ttk.Button(details_frame, text="No investment schedule", command=open_investment_year_window)
        no_investment_button.grid(row=0, column=0, columnspan=2, pady=10)

    # Ensure the Save Investments button is always shown
    save_button = ttk.Button(details_frame, text="Save Investments", command=open_investment_year_window)
    save_button.grid(row=6, column=0, columnspan=2, pady=10)

    # Add a close button
    close_button = ttk.Button(project_window, text="Close", command=project_window.destroy)
    close_button.pack(pady=10)