import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from db.base_repository import BaseRepository

class DepreciationRepository(BaseRepository):
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

        # Update logic to handle query results
        if result and isinstance(result, list) and len(result) > 0:
            # Handle dict-based result (RealDictCursor)
            if isinstance(result[0], dict) and 'depreciation_id' in result[0]:
                depreciation_id = result[0]['depreciation_id']
            # Handle tuple-based result (fallback)
            elif isinstance(result[0], tuple):
                depreciation_id = result[0][0]  # Access the first element of the tuple
            else:
                depreciation_id = None
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

    def fetch_depreciation_methods(self):
        """
        Fetches depreciation method descriptions along with their IDs from the database.
        :return: A dictionary where keys are 'depreciation_id' and values are 'method_description'.
        """
        try:
            query = "SELECT depreciation_id, method_description FROM depreciation_schedules"
            results = self.execute_query(query, fetch=True)
            # Convert the list of dictionaries to a dictionary with depreciation_id as key and method_description as value
            if results and isinstance(results, list):
                # Handle dict-based results (RealDictCursor)
                if isinstance(results[0], dict):
                    return {row['depreciation_id']: row['method_description'] for row in results}
                # Handle tuple-based results (fallback)
                else:
                    return {row[0]: row[1] for row in results}
            else:
                return {}
        except Exception as e:
            print(f"Error fetching depreciation methods: {e}")
            return {}
