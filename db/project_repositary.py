from dotenv import load_dotenv
import os
import psycopg2

# Load environment variables from .env file
load_dotenv()

# Get connection string from environment variables
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    sslmode=os.getenv("DB_SSLMODE", "require")
)

# Create a cursor
cur = conn.cursor()

# Example: create table
cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        project_name TEXT,
        start_year INT,
        cost NUMERIC,
        depreciation_method TEXT,
        useful_life INT
    )
""")

conn.commit()

# Close
cur.close()
conn.close()