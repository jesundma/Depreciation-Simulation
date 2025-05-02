import tkinter as tk
from tkinter import ttk
from .save_project_window import open_save_project_window
from .open_project_window import open_open_project_window
from .setup_window import setup_database, setup_depreciation_window, setup_test_database
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_db():
    try:
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            raise ValueError("DATABASE_URL is not set in environment variables.")

        # Connect to the database
        conn = psycopg2.connect(db_url)

        # Check if SSL is used
        ssl_status = conn.get_parameter_status('ssl')
        print("Connection successful!")
        print(f"SSL connection: {ssl_status}")

        conn.close()

    except psycopg2.OperationalError as oe:
        print(f"Operational error occurred: {oe}")
    except psycopg2.DatabaseError as de:
        print(f"Database error occurred: {de}")
    except Exception as e:
        print(f"Database connection failed: {e}")

def open_database_status_window():
    status_window = tk.Toplevel()
    status_window.title("Database Status")
    status_window.geometry("400x300")

    text_area = tk.Text(status_window, wrap=tk.WORD, font=("Arial", 12), height=15, width=50)
    text_area.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(status_window, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.config(yscrollcommand=scrollbar.set)

    def update_status(message):
        text_area.insert(tk.END, message + "\n")
        text_area.see(tk.END)
        status_window.update_idletasks()

    try:
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            raise ValueError("DATABASE_URL is not set in environment variables.")

        update_status("Opening database connection...")
        conn = psycopg2.connect(db_url)

        update_status("Executing test query...")
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")

        update_status("Closing database connection...")
        conn.close()

        update_status("Database connection closed successfully.")

    except psycopg2.OperationalError as oe:
        update_status(f"Operational error occurred:\n{oe}")
    except psycopg2.DatabaseError as de:
        update_status(f"Database error occurred:\n{de}")
    except Exception as e:
        update_status(f"Database operation failed:\n{e}")

    close_button = ttk.Button(status_window, text="Close", command=status_window.destroy)
    close_button.pack(pady=20)

def setup_database():
    status_window = tk.Toplevel()
    status_window.title("Database Setup Status")
    status_window.geometry("400x300")

    text_area = tk.Text(status_window, wrap=tk.WORD, font=("Arial", 12), height=15, width=50)
    text_area.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(status_window, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.config(yscrollcommand=scrollbar.set)

def main_window():
    def open_project():
        open_open_project_window(root)

    def save_project():
        open_save_project_window(root)

    def setup_database():
        setup_database_window()

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
    investment_menu.add_command(label="Create Project", command=save_project)  # Updated label from 'Save Project' to 'Create Project'
    menu_bar.add_cascade(label="Investment Projects", menu=investment_menu)

    # Add Setup and Maintenance menu
    database_menu = tk.Menu(menu_bar, tearoff=0)
    database_menu.add_command(label="Database Setup", command=setup_database_window)
    database_menu.add_command(label="Depreciation Setup", command=setup_depreciation_window)
    database_menu.add_command(label="Test Database Setup", command=setup_test_database)  # Modify the label for the test database setup menu item
    menu_bar.add_cascade(label="Setup and Maintenance", menu=database_menu)

    root.config(menu=menu_bar)

    welcome_label = ttk.Label(root, text="Welcome to the Project Manager", font=("Arial", 16))
    welcome_label.pack(pady=50)

    root.mainloop()

if __name__ == "__main__":
    main_window()
