import tkinter as tk
from tkinter import ttk
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database_window():
    status_window = tk.Toplevel()
    status_window.title("Database Setup Status")
    status_window.geometry("400x300")

    # Replace the status_label with a scrolling text widget
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

        update_status("Creating new tables...")
        cur.execute("""
            CREATE TABLE projects (
                project_id TEXT PRIMARY KEY,
                branch TEXT,
                operations TEXT,
                description TEXT
            );

            CREATE TABLE investments (
                project_id TEXT REFERENCES projects(project_id),
                yearly_investments JSONB,
                PRIMARY KEY (project_id)
            );

            CREATE TABLE depreciation_schedules (
                project_id TEXT REFERENCES projects(project_id),
                schedule JSONB,
                PRIMARY KEY (project_id)
            );

            CREATE TABLE calculated_depreciations (
                project_id TEXT REFERENCES projects(project_id),
                calculated_values JSONB,
                PRIMARY KEY (project_id)
            );
        """)

        conn.commit()
        cur.close()
        conn.close()

        update_status("Database setup completed successfully!")

    except Exception as e:
        update_status(f"Database setup failed:\n{e}")

    close_button = ttk.Button(status_window, text="Close", command=status_window.destroy)
    close_button.pack(pady=20)