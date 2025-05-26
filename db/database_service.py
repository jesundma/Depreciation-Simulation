import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from dotenv import load_dotenv
import os
from gui.status_window import StatusWindow

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

    def setup_database(self):
        """
        Set up the database by creating new tables only if they do not already exist.
        """
        try:
            conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            # Create tables only if they do not already exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS depreciation_schedules (
                    depreciation_id SERIAL PRIMARY KEY,
                    depreciation_percentage NUMERIC,
                    depreciation_years INT,
                    method_description TEXT
                );

                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    branch TEXT,
                    operations TEXT,
                    description TEXT,
                    depreciation_method INT REFERENCES depreciation_schedules(depreciation_id)
                );

                CREATE TABLE IF NOT EXISTS project_classifications (
                    project_id TEXT PRIMARY KEY REFERENCES projects(project_id),
                    importance INT,
                    type INT
                );

                CREATE TABLE IF NOT EXISTS investments (
                    project_id TEXT REFERENCES projects(project_id),
                    year INT,
                    investment_amount NUMERIC,
                    depreciation_start_year INT,
                    PRIMARY KEY (project_id, year)
                );

                CREATE TABLE IF NOT EXISTS calculated_depreciations (
                    project_id TEXT REFERENCES projects(project_id),
                    year INT,
                    depreciation_value NUMERIC,
                    remaining_value NUMERIC,
                    PRIMARY KEY (project_id, year)
                );
            """)

            # Ensure indexes exist for optimized queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_project_id ON projects (project_id);
                CREATE INDEX IF NOT EXISTS idx_year ON investments (year);
            """)

            conn.commit()
            cur.close()
            conn.close()

            return "Database setup completed successfully!"

        except Exception as e:
            return f"Database setup failed: {e}"

    def get_investment_schedule(self, project_id):
        """
        Fetch the investment schedule for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of investments with year, amount, and depreciation start year.
        """
        query = """
        SELECT 
            COALESCE(idp.start_year, i.year) AS year, 
            i.investment_amount, 
            idp.start_year AS start_year
        FROM investment_depreciation_periods idp
        FULL OUTER JOIN investments i
        ON idp.project_id = i.project_id AND idp.start_year = i.year
        WHERE idp.project_id = %s OR i.project_id = %s
        ORDER BY year
        """
        params = (project_id, project_id)
        return self.execute_query(query, params, fetch=True)

    def save_project(self, project):
        """
        Save or update a project in the database.
        :param project: A Project object containing project details.
        """
        query = """
            INSERT INTO projects (project_id, branch, operations, description, depreciation_method)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE
            SET branch = EXCLUDED.branch,
                operations = EXCLUDED.operations,
                description = EXCLUDED.description,
                depreciation_method = EXCLUDED.depreciation_method;
        """
        params = (project.project_id, project.branch, project.operations, project.description, project.depreciation_method)
        self.execute_query(query, params)

    def save_investments(self, project_id, investments):
        """
        Save yearly investments and depreciation start years for a given project ID.
        :param project_id: The ID of the project.
        :param investments: A dictionary where the key is the year and the value is a tuple of (investment_amount, depreciation_start_year).
        """
        query = """
            INSERT INTO investments (project_id, year, investment_amount, depreciation_start_year)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id, year) DO UPDATE
            SET investment_amount = EXCLUDED.investment_amount,
                depreciation_start_year = EXCLUDED.depreciation_start_year;
        """
        for year, (amount, start_year) in investments.items():
            params = (project_id, year, amount, start_year)
            self.execute_query(query, params)

    def save_investment_details(self, project_id, investments):
        """
        Save or update investment details, including amounts and depreciation start years.
        :param project_id: The ID of the project.
        :param investments: A dictionary where the key is the year and the value is a tuple of (investment_amount, depreciation_start_year).
        """
        query = """
            INSERT INTO investments (project_id, year, investment_amount, depreciation_start_year)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id, year) DO UPDATE
            SET investment_amount = EXCLUDED.investment_amount,
                depreciation_start_year = EXCLUDED.depreciation_start_year;
        """
        for year, (amount, start_year) in investments.items():
            params = (project_id, year, amount, start_year)
            self.execute_query(query, params)

    def save_yearly_investments(self, project_id, investments):
        """
        Save yearly investments for a given project ID without requiring depreciation_start_year.
        :param project_id: The ID of the project.
        :param investments: A dictionary where the key is the year and the value is the investment amount.
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

    def save_depreciation_start_years(self, project_id, depreciation_start_years):
        """
        Save depreciation start years for a given project ID.
        :param project_id: The ID of the project.
        :param depreciation_start_years: A dictionary mapping years to depreciation start years.
        """
        query = """
            UPDATE investments
            SET depreciation_start_year = %s
            WHERE project_id = %s AND year = %s;
        """
        for year, start_year in depreciation_start_years.items():
            params = (start_year, project_id, year)
            self.execute_query(query, params)

    def save_depreciation_year(self, project_id, year, depreciation_year):
        """
        Save a single depreciation year to the investments table.
        :param project_id: The ID of the project.
        :param year: The year of the investment.
        :param depreciation_year: The depreciation year to save.
        """
        query = """
            UPDATE investments
            SET depreciation_start_year = %s
            WHERE project_id = %s AND year = %s;
        """
        params = (depreciation_year, project_id, year)
        self.execute_query(query, params)

    def save_depreciation_start_year(self, project_id, year, depreciation_year):
        """
        Save or update the depreciation start year for a specific project and year in the investments table.
        :param project_id: The ID of the project.
        :param year: The year of the investment.
        :param depreciation_year: The depreciation start year to save.
        """
        query = """
            UPDATE investments
            SET depreciation_start_year = %s
            WHERE project_id = %s AND year = %s;
        """
        params = (depreciation_year, project_id, year)
        self.execute_query(query, params)

    def save_depreciation_schedule(self, depreciation_percentage, depreciation_years, method_description):
        """
        Save or update a general depreciation schedule in the database.
        :param depreciation_percentage: Depreciation percentage (can be None).
        :param depreciation_years: Depreciation years (can be None).
        :param method_description: Description of the depreciation method.
        """
        # Check if a record with the same depreciation_percentage or depreciation_years exists
        check_query = """
            SELECT depreciation_id FROM depreciation_schedules
            WHERE depreciation_percentage = %s OR depreciation_years = %s
        """
        params = (depreciation_percentage, depreciation_years)
        result = self.execute_query(check_query, params, fetch=True)

        # Update logic to handle query results as tuples
        if result and isinstance(result, list) and len(result) > 0:
            depreciation_id = result[0][0]  # Access the first element of the tuple
        else:
            depreciation_id = None

        if depreciation_id:
            # Update existing record
            update_query = """
                UPDATE depreciation_schedules
                SET depreciation_percentage = %s,
                    depreciation_years = %s,
                    method_description = %s
                WHERE depreciation_id = %s
            """
            update_params = (depreciation_percentage, depreciation_years, method_description, depreciation_id)
            self.execute_query(update_query, update_params)
        else:
            # Insert new record
            insert_query = """
                INSERT INTO depreciation_schedules (depreciation_percentage, depreciation_years, method_description)
                VALUES (%s, %s, %s)
            """
            insert_params = (depreciation_percentage, depreciation_years, method_description)
            self.execute_query(insert_query, insert_params)

    def create_tables(self):
        """
        Create all necessary tables in the database.
        """
        query_create_tables = """
            CREATE TABLE IF NOT EXISTS depreciation_schedules (
                depreciation_id SERIAL PRIMARY KEY,
                depreciation_percentage NUMERIC,
                depreciation_years INT,
                method_description TEXT
            );

            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                branch TEXT,
                operations TEXT,
                description TEXT,
                depreciation_method INT REFERENCES depreciation_schedules(depreciation_id)
            );

            CREATE TABLE IF NOT EXISTS project_classifications (
                project_id TEXT PRIMARY KEY REFERENCES projects(project_id),
                importance INT,
                type INT
            );

            CREATE TABLE IF NOT EXISTS investments (
                project_id TEXT REFERENCES projects(project_id),
                year INT,
                investment_amount NUMERIC,
                depreciation_start_year INT,
                PRIMARY KEY (project_id, year)
            );

            CREATE TABLE IF NOT EXISTS calculated_depreciations (
                project_id TEXT REFERENCES projects(project_id),
                year INT,
                depreciation_value NUMERIC,
                remaining_value NUMERIC,
                PRIMARY KEY (project_id, year)
            );
        """
        self.execute_query(query_create_tables)

        # Ensure indexes exist for optimized queries
        query_create_indexes = """
            CREATE INDEX IF NOT EXISTS idx_project_id ON projects (project_id);
            CREATE INDEX IF NOT EXISTS idx_year ON investments (year);
        """
        self.execute_query(query_create_indexes)

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

    def fetch_depreciation_methods(self):
        """
        Fetches depreciation method descriptions along with their IDs from the database.
        :return: A dictionary where keys are 'depreciation_id' and values are 'method_description'.
        """
        try:
            query = "SELECT depreciation_id, method_description FROM depreciation_schedules"
            results = self.execute_query(query, fetch=True)
            # Convert the list of dictionaries to a dictionary with depreciation_id as key and method_description as value
            # Ensure results are iterable before using comprehensions
            if results and isinstance(results, list):
                return {row[0]: row[1] for row in results}  # Access tuple elements by index
            else:
                return {}
        except Exception as e:
            print(f"Error fetching depreciation methods: {e}")
            return {}

    def has_calculated_depreciations(self, project_id):
        """
        Check if there are calculated depreciations for the given project ID.
        :param project_id: The ID of the project.
        :return: True if calculated depreciations exist, False otherwise.
        """
        query = "SELECT EXISTS (SELECT 1 FROM calculated_depreciations WHERE project_id = %s AND remaining_value IS NOT NULL)"
        params = (project_id,)
        result = self.execute_query(query, params, fetch=True)

        # Debug: Print the query result to inspect its structure
        print("[DEBUG] Query result for has_calculated_depreciations:", result)

        # Handle cases where results might be None or unexpected
        if result and isinstance(result, list) and len(result) > 0:
            # Check if the result is a RealDictRow and access the 'exists' key
            if isinstance(result[0], dict) and 'exists' in result[0]:
                return bool(result[0]['exists'])
            elif isinstance(result[0], tuple):
                return bool(result[0][0])  # Fallback for tuple-based results
    
        # If no valid result is found, return False without treating it as an error
        print("[INFO] No calculated depreciations found or unexpected result structure.")
        return False
    def get_depreciation_method_details(self, project_id):
        """
        Fetch the depreciation method details (percentage and years) for a given project ID.
        :param project_id: The ID of the project.
        :return: A dictionary containing depreciation_percentage and depreciation_years.
        """
        query = """
            SELECT depreciation_percentage, depreciation_years 
            FROM depreciation_schedules 
            WHERE depreciation_id = (
                SELECT depreciation_method 
                FROM projects 
                WHERE project_id = %s
            )
        """
        params = (project_id,)
        result = self.execute_query(query, params, fetch=True)
        return result[0] if result else None

    def save_calculated_depreciations(self, project_id, df):
        """
        Save the calculated depreciation results to the calculated_depreciations table.
        :param project_id: The ID of the project.
        :param df: A pandas DataFrame containing the depreciation results.
        """
        # Debugging: Print the DataFrame before saving
        print("[DEBUG] DataFrame to be saved:")
        print(df.head())

        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()

        # Ensure required columns exist
        if not {'year', 'depreciation', 'remaining asset value'}.issubset(df.columns):
            raise ValueError("Missing required columns in the DataFrame: 'year', 'depreciation', 'remaining asset value'")

        query = """
            INSERT INTO calculated_depreciations (project_id, year, depreciation_value, remaining_value)
            VALUES %s
            ON CONFLICT (project_id, year) DO UPDATE
            SET depreciation_value = EXCLUDED.depreciation_value,
                remaining_value = EXCLUDED.remaining_value;
        """

        # Prepare data for batch insertion
        data = [
            (
                project_id,
                int(row["year"]),
                float(row["depreciation"]),
                float(row["remaining asset value"])
            )
            for _, row in df.iterrows()
        ]

        try:
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cursor:
                    execute_values(cursor, query, data)
                    conn.commit()
            print("[INFO] Batch insertion of calculated depreciations completed successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to batch insert calculated depreciations: {e}")

    def fetch_report_data(self, project_id: str):
        """
        Fetch all investments and depreciations for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of dictionaries containing year, investment amount, and depreciation value.
        """
        query = """
            SELECT start_year AS year, 
                   COALESCE(SUM(investment_amount), 0) AS investment_amount,
                   COALESCE(SUM(depreciation_value), 0) AS depreciation_value
            FROM (
                SELECT start_year AS year, investment_amount, NULL AS depreciation_value
                FROM investment_depreciation_periods
                WHERE project_id = %s
                UNION ALL
                SELECT start_year AS year, NULL AS investment_amount, depreciation_value
                FROM calculated_depreciations
                WHERE project_id = %s
            ) AS combined
            GROUP BY year
            ORDER BY year;
        """
        params = (project_id, project_id)
        return self.execute_query(query, params, fetch=True)

    def get_depreciation_report(self, project_id: str):
        """
        Fetch all investments and depreciations for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of dictionaries containing year, investment amount, and depreciation value.
        """
        query = """
            SELECT year, 
                   COALESCE(SUM(investment_amount), 0) AS investment_amount,
                   COALESCE(SUM(depreciation_value), 0) AS depreciation_value
            FROM (
                SELECT year, investment_amount, NULL AS depreciation_value
                FROM investments
                WHERE project_id = %s
                UNION ALL
                SELECT year, NULL AS investment_amount, depreciation_value
                FROM calculated_depreciations
                WHERE project_id = %s
            ) AS combined
            GROUP BY year
            ORDER BY year;
        """
        params = (project_id, project_id)
        return self.execute_query(query, params, fetch=True)

    def get_all_depreciation_reports(self):
        """
        Fetch all investments and depreciations across all projects.
        :return: A list of dictionaries containing project ID, year, investment amount, and depreciation value.
        """
        query = """
            SELECT project_id, year, 
                   COALESCE(SUM(investment_amount), 0) AS investment_amount,
                   COALESCE(SUM(depreciation_value), 0) AS depreciation_value
            FROM (
                SELECT project_id, year, investment_amount, NULL AS depreciation_value
                FROM investment_depreciation_periods
                UNION ALL
                SELECT project_id, year, NULL AS investment_amount, depreciation_value
                FROM calculated_depreciations
            ) AS combined
            GROUP BY project_id, year
            ORDER BY year;
        """
        return self.execute_query(query, fetch=True)

    def get_projects_data(self):
        """
        Fetch all data from the projects table.
        :return: A list of dictionaries containing project details.
        """
        query = "SELECT * FROM projects"
        return self.execute_query(query, fetch=True)

    def save_projects_batch(self, projects):
        """
        Save multiple projects in the database in a single batch.
        :param projects: A list of tuples (project_id, branch, operations, description, depreciation_method).
        """
        try:
            # Initialize StatusWindow dynamically
            status_window = StatusWindow("Database Operations Status")
            status_window.update_status(f"[INFO] Attempting to save {len(projects)} projects in batch.")

            # Extract project IDs from the incoming data
            project_ids = [str(project[0]) for project in projects]  # Ensure all IDs are strings

            # Use psycopg2's execute_values for efficient batch inserts/updates
            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # Insert or update rows
                    query_upsert = """
                        INSERT INTO projects (project_id, branch, operations, description, depreciation_method)
                        VALUES %s
                        ON CONFLICT (project_id) DO UPDATE
                        SET branch = EXCLUDED.branch,
                            operations = EXCLUDED.operations,
                            description = EXCLUDED.description,
                            depreciation_method = EXCLUDED.depreciation_method;
                    """
                    execute_values(cur, query_upsert, projects)

                    # Delete rows not in the incoming data
                    query_delete = """
                        DELETE FROM projects
                        WHERE project_id NOT IN %s;
                    """
                    # Execute the DELETE query and get the number of rows removed
                    cur.execute(query_delete, (tuple(project_ids),))
                    removed_rows = cur.rowcount
                    conn.commit()

                    # Update the StatusWindow with the correct number of rows removed
                    status_window.update_status(f"[INFO] Successfully saved {len(projects)} projects in batch and removed {removed_rows} obsolete rows.")
        except Exception as e:
            print(f"[ERROR] Failed to save projects batch: {repr(e)}")
            raise

    def save_investments_batch(self, investments):
        """
        Save multiple investments in the database in a single batch.
        :param investments: A list of tuples (project_id, year, investment_amount).
        """
        query = """
            INSERT INTO investments (project_id, year, investment_amount)
            VALUES %s
            ON CONFLICT (project_id, year) DO UPDATE
            SET investment_amount = EXCLUDED.investment_amount;
        """
        try:
            # Initialize StatusWindow dynamically
            status_window = StatusWindow("Database Operations Status")
            status_window.update_status(f"[INFO] Attempting to save {len(investments)} investments in batch.")

            # Extract project IDs from the incoming data
            project_ids = [str(investment[0]) for investment in investments]  # Ensure all IDs are strings

            # Use psycopg2's execute_values for efficient batch inserts
            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # Insert or update rows
                    execute_values(cur, query, investments)

                    # Ensure project_ids is not empty to avoid SQL syntax errors
                    if project_ids:
                        query_delete = """
                            DELETE FROM investment_depreciation_periods
                            WHERE project_id NOT IN %s;
                        """
                        # Execute the DELETE query and get the number of rows removed
                        cur.execute(query_delete, (tuple(project_ids),))
                        removed_rows = cur.rowcount
                        conn.commit()

                        # Update the StatusWindow with the correct number of rows removed
                        status_window.update_status(f"[INFO] Successfully saved {len(investments)} investments in batch and removed {removed_rows} obsolete rows.")
                    else:
                        print("[WARNING] No project IDs provided. Skipping deletion of obsolete rows.")
        except psycopg2.errors.ForeignKeyViolation as e:
            # Initialize StatusWindow dynamically if not already initialized
            status_window = StatusWindow("Database Operations Status")
            if "investments_project_id_fkey" in str(e):
                status_window.update_status("[ERROR] ForeignKeyViolation: Some project IDs in investments are missing in the projects table. Please run 'Import Projects' to resolve this issue.")
            print(f"[ERROR] ForeignKeyViolation: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to save investments batch: {repr(e)}")
            raise

    def save_project_classifications(self, classifications):
        """
        Save or update project classifications in the database.
        :param classifications: A list of tuples (project_id, importance, type).
        """
        try:
            # Initialize StatusWindow dynamically
            status_window = StatusWindow("Database Operations Status")
            status_window.update_status(f"[INFO] Attempting to save {len(classifications)} project classifications in batch.")

            # Extract project IDs from the incoming data
            project_ids = [str(classification[0]) for classification in classifications]  # Ensure all IDs are strings

            # Use psycopg2's execute_values for efficient batch inserts/updates
            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # Insert or update rows
                    query_upsert = """
                        INSERT INTO project_classifications (project_id, importance, type)
                        VALUES %s
                        ON CONFLICT (project_id) DO UPDATE
                        SET importance = EXCLUDED.importance,
                            type = EXCLUDED.type;
                    """
                    execute_values(cur, query_upsert, classifications)

                    # Ensure project_ids is not empty to avoid SQL syntax errors
                    if project_ids:
                        query_delete = """
                            DELETE FROM project_classifications
                            WHERE project_id NOT IN %s;
                        """
                        cur.execute(query_delete, (tuple(project_ids),))
                    else:
                        print("[WARNING] No project IDs provided. Skipping deletion of obsolete rows.")

                    conn.commit()

            # Log success
            status_window.update_status(f"[INFO] Successfully saved {len(classifications)} project classifications in batch and removed obsolete rows.")
        except Exception as e:
            print(f"[ERROR] Failed to save project classifications batch: {repr(e)}")
            raise

    def save_depreciation_years_batch(self, depreciation_years_data):
        """
        Save multiple depreciation years in the database in a single batch.
        :param depreciation_years_data: A list of tuples (project_id, year, depreciation_year).
        """
        query = """
            UPDATE investments
            SET depreciation_start_year = data.depreciation_year
            FROM (VALUES %s) AS data(project_id, year, depreciation_year)
            WHERE investments.project_id = data.project_id AND investments.year = data.year;
        """
        try:
            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, depreciation_years_data, template=None)
                    conn.commit()
        except Exception as e:
            print(f"[ERROR] Failed to save depreciation years batch: {e}")
            raise

    def save_project_classifications_batch(self, classifications):
        """
        Save or update project classifications in the database in a single batch.
        :param classifications: A list of tuples (project_id, importance, type).
        """
        query = """
            INSERT INTO project_classifications (project_id, importance, type)
            VALUES %s
            ON CONFLICT (project_id) DO UPDATE
            SET importance = EXCLUDED.importance,
                type = EXCLUDED.type;
        """
        try:
            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    print(f"[DEBUG] Attempting to save {len(classifications)} project classifications in batch.")
                    execute_values(cur, query, classifications)

                    # Extract project IDs from the incoming data
                    project_ids = [str(classification[0]) for classification in classifications]

                    # Ensure project_ids is not empty to avoid SQL syntax errors
                    if project_ids:
                        query_delete = """
                            DELETE FROM project_classifications
                            WHERE project_id NOT IN %s;
                        """
                        # Execute the DELETE query and get the number of rows removed
                        cur.execute(query_delete, (tuple(project_ids),))
                        removed_rows = cur.rowcount
                        conn.commit()

                        # Initialize StatusWindow dynamically
                        status_window = StatusWindow("Database Operations Status")

                        # Update the StatusWindow with the correct number of rows removed
                        status_window.update_status(f"[INFO] Successfully saved {len(classifications)} classifications in batch and removed {removed_rows} obsolete rows.")

                    else:
                        print("[WARNING] No project IDs provided. Skipping deletion of obsolete rows.")

                    print(f"[DEBUG] Successfully saved {len(classifications)} project classifications in batch.")
        except psycopg2.errors.ForeignKeyViolation as e:
            # Initialize StatusWindow dynamically if not already initialized
            status_window = StatusWindow("Database Operations Status")
            if "project_classifications_project_id_fkey" in str(e):
                status_window.update_status("[ERROR] ForeignKeyViolation: Some project IDs in classifications are missing in the projects table. Please run 'Import Projects' to resolve this issue.")
            print(f"[ERROR] ForeignKeyViolation: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to save project classifications batch: {e}")
            raise

    def get_all_project_ids(self):
        """
        Fetch all project IDs from the database.
        :return: A list of project IDs.
        """
        query = "SELECT project_id FROM projects"
        results = self.execute_query(query, fetch=True)
        # Ensure results are iterable before using comprehensions
        if results and isinstance(results, list):
            return [row[0] for row in results]  # Access the first element of each tuple
        else:
            return []

    def get_project_classifications(self):
        """
        Fetch all project classifications from the database.
        :return: A list of dictionaries containing project_id, importance, and type.
        """
        query = "SELECT project_id, importance, type FROM project_classifications"
        return self.execute_query(query, fetch=True)

    def clean_database(self):
        """
        Clean the database by dropping all tables in the public schema.
        """
        try:
            print("Opening database connection...")
            conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
            cur = conn.cursor()

            print("Clearing all tables...")
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

            print("Database cleaning completed successfully!")
        except Exception as e:
            print(f"Database cleaning failed:\n{e}")
            raise

    def clear_table(self, table_name: str):
        """
        Clears all data from the specified table, including dependent tables.
        :param table_name: The name of the table to clear.
        """
        query = f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"
        self.execute_query(query)
        print(f"[INFO] Table '{table_name}' and its dependencies have been cleared.")

    def fetch_grouped_project_data(self):
        """
        Fetch and group project data by importance, type, branch, operations, and year.
        :return: A list of dictionaries containing grouped project data.
        """
        query = """
            SELECT 
                pc.importance,
                pc.type,
                p.branch,
                p.operations,
                p.project_id,
                i.year,
                SUM(i.investment_amount) AS total_investment,
                cd.description AS importance_description,
                tc.description AS type_description,
                p.description AS project_description
            FROM 
                project_classifications pc
            JOIN 
                projects p ON pc.project_id = p.project_id
            JOIN 
                investments i ON p.project_id = i.project_id
            LEFT JOIN 
                classification_descriptions cd ON pc.importance = cd.classification_id
            LEFT JOIN 
                type_classification tc ON pc.type = tc.type_id
            GROUP BY 
                pc.importance, pc.type, p.branch, p.operations, p.project_id, i.year, cd.description, tc.description, p.description
            ORDER BY 
                pc.importance, pc.type, p.branch, p.operations, p.project_id, i.year;
        """
        return self.execute_query(query, fetch=True)

    def save_depreciation_starts_batch(self, depreciation_starts):
        """
        Save multiple depreciation start years and months in the investment_depreciation_periods table in a single batch.
        Removes rows for (project_id, start_year) pairs not present in the new data.
        :param depreciation_starts: A list of tuples (project_id, start_year, start_month).
        """
        query_upsert = """
            INSERT INTO investment_depreciation_periods (project_id, start_year, start_month)
            VALUES %s
            ON CONFLICT (project_id, start_year) DO UPDATE
            SET start_month = EXCLUDED.start_month;
        """
        try:
            status_window = StatusWindow("Database Operations Status")
            status_window.update_status(f"[INFO] Attempting to save {len(depreciation_starts)} depreciation starts in batch.")

            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query_upsert, depreciation_starts)

                    # Prepare set of (project_id, start_year) pairs to keep
                    keep_pairs = [(str(t[0]), int(t[1])) for t in depreciation_starts]
                    if keep_pairs:
                        # Build the ROW constructor string and parameters
                        row_placeholders = ', '.join(['ROW(%s, %s)'] * len(keep_pairs))
                        flat_params = [item for pair in keep_pairs for item in pair]
                        delete_query = f"""
                            DELETE FROM investment_depreciation_periods
                            WHERE (project_id, start_year) NOT IN ({row_placeholders});
                        """
                        cur.execute(delete_query, flat_params)
                        removed_rows = cur.rowcount
                    else:
                        removed_rows = 0
                    conn.commit()

            status_window.update_status(f"[INFO] Successfully saved {len(depreciation_starts)} depreciation starts in batch and removed {removed_rows} obsolete rows.")
        except Exception as e:
            print(f"[ERROR] Failed to save depreciation starts batch: {e}")
            raise