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
        query = "SELECT EXISTS (SELECT 1 FROM calculated_depreciations WHERE project_id = %s AND remainder IS NOT NULL)"
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
        required_columns = {'year', 'month', 'depreciation_base', 'monthly_depreciation', 'remainder'}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"Missing required columns in the DataFrame: {required_columns - set(df.columns)}")

        query = """
            INSERT INTO calculated_depreciations (project_id, year, month, depreciation_base, monthly_depreciation, remainder, cost_center)
            VALUES %s
            ON CONFLICT (project_id, year, month) DO UPDATE
            SET depreciation_base = EXCLUDED.depreciation_base,
                monthly_depreciation = EXCLUDED.monthly_depreciation,
                remainder = EXCLUDED.remainder,
                cost_center = EXCLUDED.cost_center;
        """

        # Prepare data for batch insertion
        data = [
            (
                project_id,
                int(row["year"]),
                int(row["month"]),
                float(row["depreciation_base"]),
                float(row["monthly_depreciation"]),
                float(row["remainder"]), 
                str(row["cost_center"])
            )
            for _, row in df.iterrows()
        ]

        # Debugging: Log the prepared data for batch insertion
        print("[DEBUG] Prepared data for batch insertion:")
        for record in data:
            print(record)

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

    def get_depreciation_percentage(self, project_id):
        """
        Fetch the depreciation percentage for a given project ID.
        :param project_id: The ID of the project.
        :return: Depreciation percentage value.
        """
        query = """
        SELECT ds.depreciation_percentage
        FROM depreciation_schedules ds
        JOIN projects p ON ds.depreciation_id = p.depreciation_method
        WHERE p.project_id = %s;
        """
        params = (project_id,)
        result = self.execute_query(query, params, fetch=True)
        return result[0]['depreciation_percentage'] if result else None

    def delete_calculated_depreciations(self, project_id):
        """
        Delete all calculated depreciations for a given project.
        """
        query = "DELETE FROM calculated_depreciations WHERE project_id = %s"
        self.execute_query(query, (project_id,))

    def get_all_depreciations_by_project(self, project_id):
        """
        Fetch all depreciation rows for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of dictionaries containing depreciation data.
        """
        query = """
            SELECT * FROM calculated_depreciations
            WHERE project_id = %s
        """
        params = (project_id,)
        result = self.execute_query(query, params, fetch=True)
        return result if result else []
