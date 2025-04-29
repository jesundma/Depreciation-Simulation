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
        # Connect to DB and save project
        pass

    @staticmethod
    def load_from_database(project_id: str) -> Project:
        # Connect to DB and load project
        pass

    @staticmethod
    def calculate_depreciation(project: Project):
        # Apply some depreciation logic
        pass