# This file contains the logic for the Database Setup window
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_database():
    status_window = tk.Toplevel()
    status_window.title("Clean Database Status")
    status_window.geometry("400x300")

    def confirm_cleaning():
        text_area.delete(1.0, tk.END)  # Clear the text area

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
            cur = conn.cursor()

            update_status("Clearing all tables...")
            cur.execute("""
                DO $$
                DECLARE
                    table_name text;
                BEGIN
                    FOR table_name IN
                        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                    LOOP
                        EXECUTE format('DROP TABLE IF EXISTS %I CASCADE', table_name);
                    END LOOP;
                END;
                $$;
            """)

            conn.commit()
            cur.close()
            conn.close()

            update_status("Database cleaning completed successfully!")

        except Exception as e:
            update_status(f"Database cleaning failed:\n{e}")

    def cancel_cleaning():
        status_window.destroy()

    warning_label = tk.Label(status_window, text="Do you wish to proceed cleaning the database?", font=("Arial", 12), fg="red")
    warning_label.pack(pady=10)

    button_frame = tk.Frame(status_window)
    button_frame.pack(pady=10)

    yes_button = tk.Button(button_frame, text="Yes", command=confirm_cleaning)
    yes_button.pack(side=tk.LEFT, padx=5)

    no_button = tk.Button(button_frame, text="No", command=cancel_cleaning)
    no_button.pack(side=tk.LEFT, padx=5)

    text_area = tk.Text(status_window, wrap=tk.WORD, font=("Arial", 12), height=15, width=50)
    text_area.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(status_window, command=text_area.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area.config(yscrollcommand=scrollbar.set)

    close_button = ttk.Button(status_window, text="Close", command=status_window.destroy)
    close_button.pack(pady=20)