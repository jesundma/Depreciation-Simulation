import tkinter as tk
from tkinter import ttk
from services.project_service import DatabaseService

def display_project_window(project):
    """
    Display a project in an independent window.
    :param project: Dictionary containing project details.
    """
    project_window = tk.Toplevel()
    project_window.title(f"Project: {project['project_id']}")
    project_window.geometry("400x400")

    # Display project details
    ttk.Label(project_window, text="Project Details", font=("Arial", 14, "bold")).pack(pady=10)

    details_frame = ttk.Frame(project_window)
    details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    ttk.Label(details_frame, text="Project ID:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['project_id']).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

    ttk.Label(details_frame, text="Branch:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['branch']).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

    ttk.Label(details_frame, text="Operations:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['operations']).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

    ttk.Label(details_frame, text="Description:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    ttk.Label(details_frame, text=project['description'], wraplength=300, justify=tk.LEFT).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

    # Query investment schedule using DatabaseService
    db_service = DatabaseService()
    investments = db_service.get_investment_schedule(project['project_id'])

    if investments:
        ttk.Label(details_frame, text="Investment Schedule:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        for idx, investment in enumerate(investments, start=5):
            ttk.Label(details_frame, text=f"Year {investment['year']}:", font=("Arial", 10)).grid(row=idx, column=0, sticky=tk.W, padx=5, pady=5)
            ttk.Label(details_frame, text=f"{investment['investment_amount']}" ).grid(row=idx, column=1, sticky=tk.W, padx=5, pady=5)
    else:
        # Display a button indicating no investment schedule
        no_investment_button = ttk.Button(details_frame, text="No investment schedule", command=lambda: print("No investments available for this project."))
        no_investment_button.grid(row=4, column=0, columnspan=2, pady=10)

    # Add a close button
    close_button = ttk.Button(project_window, text="Close", command=project_window.destroy)
    close_button.pack(pady=10)