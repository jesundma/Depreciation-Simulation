import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def open_save_project_window(root):
    def save_data():
        id1 = entry_id1.get()
        id2 = entry_id2.get()
        try:
            id3 = int(entry_id3.get())
        except ValueError:
            messagebox.showerror("Input Error", "ID3 must be an integer.")
            return
        description = text_field.get("1.0", tk.END).strip()

        messagebox.showinfo("Data Saved", "Your data has been saved successfully.")
        close_window()

    def close_window():
        popup.destroy()
        root.attributes('-disabled', False)

    root.attributes('-disabled', True)
    popup = tk.Toplevel(root)
    popup.title("Save Project")
    popup.geometry("500x400")

    ttk.Label(popup, text="ID1 (Text):").pack(pady=(10, 0))
    entry_id1 = ttk.Entry(popup)
    entry_id1.pack()

    ttk.Label(popup, text="ID2 (Text):").pack(pady=(10, 0))
    entry_id2 = ttk.Entry(popup)
    entry_id2.pack()

    ttk.Label(popup, text="ID3 (Integer):").pack(pady=(10, 0))
    entry_id3 = ttk.Entry(popup)
    entry_id3.pack()

    ttk.Label(popup, text="Project Description:").pack(pady=(10, 0))
    text_field = tk.Text(popup, height=5, width=30)
    text_field.pack()

    save_button = ttk.Button(popup, text="Save", command=save_data)
    save_button.pack(pady=20)

    popup.protocol("WM_DELETE_WINDOW", close_window)