import tkinter as tk
from tkinter import scrolledtext, ttk

class ImportStatusWindow:
    def __init__(self, title, messages, success=True):
        self.root = tk.Toplevel()
        self.root.title(title)
        self.root.geometry('600x400')
        self.root.resizable(True, True)
        self.root.grab_set()

        # Title label
        label_text = "Import Successful" if success else "Import Failed"
        label_fg = "green" if success else "red"
        label = ttk.Label(self.root, text=label_text, font=("Arial", 16, "bold"), foreground=label_fg)
        label.pack(pady=(10, 5))

        # Scrolled text for messages
        self.text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Consolas", 11))
        self.text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        self.text.insert(tk.END, '\n'.join(messages))
        self.text.config(state=tk.DISABLED)

        # Close button
        close_btn = ttk.Button(self.root, text="Close", command=self.root.destroy)
        close_btn.pack(pady=(0, 15))

    @staticmethod
    def show(title, messages, success=True):
        win = ImportStatusWindow(title, messages, success)
        win.root.mainloop()
