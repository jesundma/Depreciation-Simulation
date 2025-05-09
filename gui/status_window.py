import tkinter as tk
from tkinter import ttk
import os
import psycopg2

class StatusWindow:
    def __init__(self, title):
        self.window = tk.Toplevel()
        self.window.title(title)
        self.window.geometry("400x300")

        self.text_area = tk.Text(self.window, wrap=tk.WORD, font=("Arial", 12), height=15, width=50)
        self.text_area.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.window, command=self.text_area.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.config(yscrollcommand=self.scrollbar.set)

        self.close_button = ttk.Button(self.window, text="Close", command=self.window.destroy)
        self.close_button.pack(pady=20)

    def update_status(self, message):
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.see(tk.END)
        self.window.update_idletasks()