import tkinter as tk
from tkinter import ttk
import os
import psycopg2

def open_status_window(title, status_messages):
    root = tk.Tk()
    root.title(title)
    root.geometry("400x300")

    text_area = tk.Text(root, wrap=tk.WORD, font=("Arial", 12), height=15, width=50)
    text_area.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(root, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.config(yscrollcommand=scrollbar.set)

    def update_status(message):
        text_area.insert(tk.END, message + "\n")
        text_area.see(tk.END)
        root.update_idletasks()

    for message in status_messages:
        update_status(message)

    close_button = ttk.Button(root, text="Close", command=root.destroy)
    close_button.pack(pady=20)

    root.mainloop()