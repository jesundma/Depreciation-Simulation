import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
from models.project_model import Project

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

class ProjectService:
    @staticmethod
    def save_to_database(project: Project):
        db_service = DatabaseService()
        query = """
            INSERT INTO projects (project_id, branch, operations, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE
            SET branch = EXCLUDED.branch,
                operations = EXCLUDED.operations,
                description = EXCLUDED.description;
        """
        params = (project.project_id, project.branch, project.operations, project.description)
        db_service.execute_query(query, params)

    @staticmethod
    def load_from_database(project_id: str) -> Project:
        # Connect to DB and load project
        pass

    @staticmethod
    def calculate_depreciation(project: Project):
        # Apply some depreciation logic
        pass

    @staticmethod
    def search_projects(project_id=None, branch=None, operations=None, description=None):
        db_service = DatabaseService()
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

        if not params:
            # If no parameters are provided, fetch all projects
            query = "SELECT * FROM projects"

        return db_service.execute_query(query, params, fetch=True)