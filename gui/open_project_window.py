import tkinter as tk
from tkinter import ttk

def open_open_project_window(root):
    def close_window():
        popup.destroy()
        root.attributes('-disabled', False)

    root.attributes('-disabled', True)
    popup = tk.Toplevel(root)
    popup.title("Open Project")
    popup.geometry("300x200")

    ttk.Label(popup, text="Open Project functionality not implemented yet.").pack(pady=20)

    popup.protocol("WM_DELETE_WINDOW", close_window)