import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class DatabaseService:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("DATABASE_URL is not set in environment variables.")

    def execute_query(self, query, params=None, fetch=False):
        """
        Executes a database query.
        :param query: SQL query to execute.
        :param params: Parameters for the query.
        :param fetch: Whether to fetch results.
        :return: Query results if fetch is True, otherwise None.
        """
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if fetch:
                        return cur.fetchall()
                    conn.commit()
        except Exception as e:
            print(f"Database query failed: {e}")
            raise

    def get_investment_schedule(self, project_id):
        """
        Fetch the investment schedule for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of investments with year and amount.
        """
        query = "SELECT year, investment_amount FROM investments WHERE project_id = %s ORDER BY year"
        params = (project_id,)
        return self.execute_query(query, params, fetch=True)

    def clear_all_tables(self):
        """
        Clear all tables in the database.
        """
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
        self.execute_query(query_clear_tables)

    def create_tables(self):
        """
        Create all necessary tables in the database.
        """
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
        self.execute_query(query_create_tables)