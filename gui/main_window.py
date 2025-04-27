import tkinter as tk
from tkinter import ttk
from .save_project_window import open_save_project_window
from .open_project_window import open_open_project_window

def main_window():
    def open_project():
        open_open_project_window(root)

    def save_project():
        open_save_project_window(root)

    def open_database():
        # Run the project_repositary.py script
        import subprocess
        subprocess.run(["python", "-m", "db.project_repositary"])

    root = tk.Tk()
    root.title("Main Menu")
    root.geometry("400x400")
    root.state('zoomed')

    menu_bar = tk.Menu(root)

    # Modify File menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Exit", command=root.quit)
    menu_bar.add_cascade(label="File", menu=file_menu)

    # Add Investment Projects menu
    investment_menu = tk.Menu(menu_bar, tearoff=0)
    investment_menu.add_command(label="Open Project", command=open_project)
    investment_menu.add_command(label="Save Project", command=save_project)
    menu_bar.add_cascade(label="Investment Projects", menu=investment_menu)

    # Add Database menu
    database_menu = tk.Menu(menu_bar, tearoff=0)
    database_menu.add_command(label="Open Database", command=open_database)
    menu_bar.add_cascade(label="Database", menu=database_menu)

    root.config(menu=menu_bar)

    welcome_label = ttk.Label(root, text="Welcome to the Project Manager", font=("Arial", 16))
    welcome_label.pack(pady=50)

    root.mainloop()

if __name__ == "__main__":
    main_window()
