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
        print(f"Executing query: {query}")
        print(f"With parameters: {params}")
        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if fetch:
                        results = cur.fetchall()
                        print(f"Query results: {results}")
                        return results
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

    def save_project(self, project):
        """
        Save or update a project in the database.
        :param project: A Project object containing project details.
        """
        query = """
            INSERT INTO projects (project_id, branch, operations, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE
            SET branch = EXCLUDED.branch,
                operations = EXCLUDED.operations,
                description = EXCLUDED.description;
        """
        params = (project.project_id, project.branch, project.operations, project.description)
        self.execute_query(query, params)

    def save_investments(self, project_id, investments):
        """
        Save yearly investments for a given project ID.
        :param project_id: The ID of the project.
        :param investments: A dictionary of year to investment amount.
        """
        query = """
            INSERT INTO investments (project_id, year, investment_amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id, year) DO UPDATE
            SET investment_amount = EXCLUDED.investment_amount;
        """
        for year, amount in investments.items():
            params = (project_id, year, amount)
            self.execute_query(query, params)

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

    def load_project(self, project_id):
        """
        Load a project from the database by its ID.
        :param project_id: The ID of the project to load.
        :return: A dictionary containing project details or None if not found.
        """
        query = "SELECT * FROM projects WHERE project_id = %s"
        params = (project_id,)
        results = self.execute_query(query, params, fetch=True)
        return results[0] if results else None

    def search_projects(self, project_id=None, branch=None, operations=None, description=None):
        """
        Search for projects in the database based on optional filters.
        :param project_id: Filter by project ID.
        :param branch: Filter by branch.
        :param operations: Filter by operations.
        :param description: Filter by description.
        :return: A list of projects matching the filters.
        """
        query = "SELECT * FROM projects WHERE TRUE"
        params = []

        if project_id:
            query += " AND project_id = %s"
            params.append(project_id)
        if branch:
            query += " AND branch ILIKE %s"
            params.append(f"%{branch}%")
        if operations:
            query += " AND operations ILIKE %s"
            params.append(f"%{operations}%")
        if description:
            query += " AND description ILIKE %s"
            params.append(f"%{description}%")

        return self.execute_query(query, params, fetch=True)