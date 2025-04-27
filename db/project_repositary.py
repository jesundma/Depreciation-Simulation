import psycopg2

# Your connection string
conn = psycopg2.connect(
    dbname="neondb",
    user="neondb_owner",
    password="npg_o5jBFkTeuR6E",
    host="ep-noisy-flower-a9t6d9h4-pooler.gwc.azure.neon.tech",
    port="5432",  # Usually 5432
    sslmode="require"
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