import tkinter as tk
from tkinter import ttk

def display_project_window(project):
    """
    Display a project in an independent window.
    :param project: Dictionary containing project details.
    """
    project_window = tk.Toplevel()
    project_window.title(f"Project: {project['project_id']}")
    project_window.geometry("400x300")

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

    # Add a close button
    close_button = ttk.Button(project_window, text="Close", command=project_window.destroy)
    close_button.pack(pady=10)