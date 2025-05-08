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
            # Create a new connection for each query
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if fetch:
                        results = cur.fetchall()
                        print(f"Query results: {results}")
                        return results
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
            conn = psycopg2.connect(self.db_url)
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
        query = "SELECT year, investment_amount, depreciation_start_year FROM investments WHERE project_id = %s ORDER BY year"
        params = (project_id,)
        return self.execute_query(query, params, fetch=True)

    def get_investment_data(self, project_id: str):
        """
        Fetch investment data for a given project.
        :param project_id: The ID of the project.
        :return: A list of investment data rows.
        """
        query = """
        SELECT year, investment_amount, depreciation_start_year
        FROM investments
        WHERE project_id = %s
        """
        return self.execute_query(query, params=(project_id,), fetch=True)

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

        if result:
            # Update existing record
            depreciation_id = result[0]['depreciation_id']
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
            return {row['depreciation_id']: row['method_description'] for row in results}
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
        return result[0]['exists'] if result else False

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
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (project_id, year) DO UPDATE
            SET depreciation_value = EXCLUDED.depreciation_value,
                remaining_value = EXCLUDED.remaining_value;
        """

        for index, row in df.iterrows():
            try:
                year = int(row["year"])
                depreciation = float(row["depreciation"])
                remaining_value = float(row["remaining asset value"])

                params = (
                    project_id,
                    year,
                    depreciation,
                    remaining_value
                )

                self.execute_query(query, params)
            except Exception as e:
                print(f"[ERROR] Failed to save row {index}: {e}")

    def fetch_report_data(self, project_id: str):
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
                FROM investments
                UNION ALL
                SELECT project_id, year, NULL AS investment_amount, depreciation_value
                FROM calculated_depreciations
            ) AS combined
            GROUP BY project_id, year
            ORDER BY project_id, year;
        """
        return self.execute_query(query, fetch=True)

    def get_projects_data(self):
        """
        Fetch all data from the projects table.
        :return: A list of dictionaries containing project details.
        """
        query = "SELECT * FROM projects"
        return self.execute_query(query, fetch=True)

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
            # Use psycopg2's execute_values for efficient batch inserts
            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    print(f"[DEBUG] Attempting to save {len(investments)} investments in batch.")
                    execute_values(cur, query, investments)
                    conn.commit()
                    print(f"[DEBUG] Successfully saved {len(investments)} investments in batch.")
        except Exception as e:
            print(f"[ERROR] Failed to save investments batch: {e}")
            raise

    def save_project_classifications(self, classifications):
        """
        Save or update project classifications in the database.
        :param classifications: A list of tuples (project_id, importance, type).
        """
        query = """
            INSERT INTO project_classifications (project_id, importance, type)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE
            SET importance = EXCLUDED.importance,
                type = EXCLUDED.type;
        """
        for project_id, importance, classification_type in classifications:
            
            # Skip entries where importance or type is still not an integer
            if not isinstance(importance, int) or not isinstance(classification_type, int):
                print(f"[WARNING] Skipping classification for project {project_id}: Importance={importance}, Type={classification_type} (Invalid data)")
                continue

            params = (project_id, importance, classification_type)
            self.execute_query(query, params)

    def save_projects_batch(self, projects):
        """
        Save multiple projects in the database in a single batch.
        :param projects: A list of tuples (project_id, branch, operations, description, depreciation_method).
        """
        query = """
            INSERT INTO projects (project_id, branch, operations, description, depreciation_method)
            VALUES %s
            ON CONFLICT (project_id) DO UPDATE
            SET branch = EXCLUDED.branch,
                operations = EXCLUDED.operations,
                description = EXCLUDED.description,
                depreciation_method = EXCLUDED.depreciation_method;
        """
        try:
            # Log the number of projects being saved
            print(f"[INFO] Attempting to save {len(projects)} projects in batch.")

            # Use psycopg2's execute_values for efficient batch inserts
            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, projects)
                    conn.commit()

            # Log success
            print(f"[INFO] Successfully saved {len(projects)} projects in batch.")
        except Exception as e:
            print(f"[ERROR] Failed to save projects batch: {e}")
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
                    conn.commit()
                    print(f"[DEBUG] Successfully saved {len(classifications)} project classifications in batch.")
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
        return [row['project_id'] for row in results]