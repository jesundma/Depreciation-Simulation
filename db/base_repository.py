import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class BaseRepository:
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
            # Create a new connection for each query
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if fetch:
                        results = cur.fetchall()
                        # Add debug statements to inspect query results
                        print(f"Query results type: {type(results)}")
                        print(f"Query results: {results}")
                        if results:
                            return results
                        else:
                            return []
                    conn.commit()
        except psycopg2.InterfaceError as e:
            print(f"[ERROR] Database connection issue: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Database query failed: {e}")
            raise
    
    @staticmethod
    def sanitize_value(val):
        """Helper method to sanitize values for database operations."""
        try:
            import pandas as pd
        except ImportError:
            pd = None
        try:
            import numpy as np
        except ImportError:
            np = None
        if pd is not None and pd.isna(val):
            return None
        if np is not None and isinstance(val, float) and np.isnan(val):
            return None
        return val
