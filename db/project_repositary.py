from dotenv import load_dotenv
import os
from services.project_service import DatabaseService

# Load environment variables from .env file
load_dotenv()

# Initialize the database service
db_service = DatabaseService()

# Example: Clear all tables
query_clear_tables = """
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
"""
# Removed the automatic execution of the query_clear_tables to ensure it is only triggered explicitly.
# db_service.execute_query(query_clear_tables)

# Example: Create tables
query_create_tables = """
    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        branch TEXT,
        operations TEXT,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS investments (
        project_id TEXT REFERENCES projects(project_id),
        year INT,
        investment_amount NUMERIC,
        PRIMARY KEY (project_id, year)
    );

    CREATE TABLE IF NOT EXISTS depreciation_schedules (
        project_id TEXT REFERENCES projects(project_id),
        year INT,
        schedule TEXT,
        PRIMARY KEY (project_id, year)
    );

    CREATE TABLE IF NOT EXISTS calculated_depreciations (
        project_id TEXT REFERENCES projects(project_id),
        year INT,
        depreciation_value NUMERIC,
        PRIMARY KEY (project_id, year)
    );
"""
db_service.execute_query(query_create_tables)