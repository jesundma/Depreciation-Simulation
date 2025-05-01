# This file contains the logic for the Depreciation Setup window
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def open_depreciation_setup_window():
    def on_percentage_change(*args):
        if percentage_var.get():
            years_entry.config(state="disabled")
        else:
            years_entry.config(state="normal")

    def on_years_change(*args):
        if years_var.get():
            percentage_entry.config(state="disabled")
        else:
            percentage_entry.config(state="normal")

    def save_depreciation_schedule():
        project_id = project_id_entry.get()
        schedule = schedule_entry.get()
        percentage = percentage_var.get()
        years = years_var.get()
        method_description = method_description_entry.get()

        if not project_id or not schedule or not method_description:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        if not percentage and not years:
            messagebox.showerror("Error", "Please fill either Percentage or Years field.")
            return

        # Save logic here
        messagebox.showinfo("Success", "Depreciation schedule saved successfully.")

    window = tk.Toplevel()
    window.title("Depreciation Setup")
    window.geometry("400x400")

    tk.Label(window, text="Project ID:").pack(pady=5)
    project_id_entry = tk.Entry(window)
    project_id_entry.pack(pady=5)

    tk.Label(window, text="Schedule:").pack(pady=5)
    schedule_entry = tk.Entry(window)
    schedule_entry.pack(pady=5)

    tk.Label(window, text="Depreciation Percentage:").pack(pady=5)
    percentage_var = tk.StringVar()
    percentage_var.trace("w", on_percentage_change)
    percentage_entry = tk.Entry(window, textvariable=percentage_var)
    percentage_entry.pack(pady=5)

    tk.Label(window, text="Depreciation Years:").pack(pady=5)
    years_var = tk.StringVar()
    years_var.trace("w", on_years_change)
    years_entry = tk.Entry(window, textvariable=years_var)
    years_entry.pack(pady=5)

    tk.Label(window, text="Method Description:").pack(pady=5)
    method_description_entry = tk.Entry(window)
    method_description_entry.pack(pady=5)

    save_button = tk.Button(window, text="Save", command=save_depreciation_schedule)
    save_button.pack(pady=20)

    close_button = tk.Button(window, text="Close", command=window.destroy)
    close_button.pack(pady=5)

    window.mainloop()