import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from collections import Counter
from db.base_repository import BaseRepository

class ProjectRepository(BaseRepository):
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

    def load_project(self, project_id):
        """
        Load a project from the database by its ID.
        :param project_id: The ID of the project to load.
        :return: A dictionary containing project details or None if not found.
        """
        query = "SELECT * FROM projects WHERE project_id = %s"
        params = (project_id,)
        results = self.execute_query(query, params, fetch=True)
        # Only return raw results; conversion to Project object should be done in the service layer
        return results[0] if results else None

    def search_projects(self, filters=None):
        """
        Search for projects in the database based on dynamic filters.
        Returns all columns defined in the Project dataclass, but replaces depreciation_method with the method description.
        :param filters: Dictionary of filters (keys are column names, values are filter values)
        :return: List of project dicts
        """
        from models.project_model import Project
        project_fields = [f.name for f in Project.__dataclass_fields__.values()]
        columns = []
        for field in project_fields:
            if field == 'depreciation_method':
                columns.append('depreciation_schedules.method_description AS depreciation_method')
            else:
                columns.append(f"projects.{field}")
        query = f"""
            SELECT {', '.join(columns)}
            FROM projects
            LEFT JOIN depreciation_schedules
                ON projects.depreciation_method = depreciation_schedules.depreciation_id
            WHERE TRUE
        """
        params = []
        if filters:
            for key, value in filters.items():
                if value is not None and value != '':
                    if key in ['branch', 'operations', 'description']:
                        query += f" AND projects.{key} ILIKE %s"
                        params.append(f"%{value}%")
                    else:
                        query += f" AND projects.{key} = %s"
                        params.append(value)
        results = self.execute_query(query, params, fetch=True)
        return results

    def get_all_project_ids(self):
        """
        Fetch all project IDs from the database.
        :return: A list of project IDs.
        """
        query = "SELECT project_id FROM projects"
        results = self.execute_query(query, fetch=True)
        # Ensure results are iterable before using comprehensions
        if results and isinstance(results, list):
            return [row["project_id"] for row in results]  # Access by key for RealDictCursor
        else:
            return []

    def save_projects_batch(self, projects, status_callback=None):
        """
        Save multiple projects in the database in a single batch.
        When importing, remove all rows from investments, investment_depreciation_periods, and calculated_depreciations
        that have obsolete project_ids (not present in the new projects list) BEFORE updating the projects table.
        :param projects: A list of tuples (project_id, branch, operations, description, depreciation_method).
        :param status_callback: Optional callback for status updates (for GUI use only).
        """
        try:
            if status_callback:
                status_callback(f"[INFO] Attempting to save {len(projects)} projects in batch.")

            # Extract new project IDs from the incoming data
            project_ids = [str(project[0]) for project in projects]  # Ensure all IDs are strings
            print(f"Incoming project count: {len(project_ids)}")
            print(f"Unique project_ids: {len(set(project_ids))}")
            duplicates = [pid for pid, count in Counter(project_ids).items() if count > 1]
            print(f"Duplicate IDs: {duplicates}")

            # --- Sanitize project tuples to replace pd.NA, np.nan, etc. with None ---
            sanitized_projects = [
                tuple(self.sanitize_value(v) for v in project)
                for project in projects
            ]
            # --- End sanitization ---

            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    # Remove obsolete project_ids from dependent tables first
                    if project_ids:
                        placeholders = ','.join(['%s'] * len(project_ids))
                        removed_rows_by_table = {}
                        # Delete from all dependent tables first, including project_classifications
                        for table in ["investments", "investment_depreciation_periods", "calculated_depreciations", "project_classifications"]:
                            delete_query = f"""
                                DELETE FROM {table}
                                WHERE project_id NOT IN ({placeholders});
                            """
                            cur.execute(delete_query, project_ids)
                            removed_rows_by_table[table] = cur.rowcount
                        # Now also remove obsolete project_ids from projects table itself
                        delete_projects_query = f"""
                            DELETE FROM projects
                            WHERE project_id NOT IN ({placeholders});
                        """
                        cur.execute(delete_projects_query, project_ids)
                        removed_rows_by_table['projects'] = cur.rowcount
                    conn.commit()

                    # Report number of rows removed by table to status_callback
                    if status_callback:
                        for table, count in removed_rows_by_table.items():
                            status_callback(f"[INFO] Removed {count} obsolete rows from {table} table.")

                    # Now upsert projects
                    from psycopg2.extras import execute_values
                    query_upsert = """
                        INSERT INTO projects (project_id, branch, operations, description, depreciation_method, cost_center)
                        VALUES %s
                        ON CONFLICT (project_id) DO UPDATE
                        SET branch = EXCLUDED.branch,
                            operations = EXCLUDED.operations,
                            description = EXCLUDED.description,
                            depreciation_method = EXCLUDED.depreciation_method,
                            cost_center = EXCLUDED.cost_center;
                    """
                    execute_values(cur, query_upsert, sanitized_projects)
                    conn.commit()

            if status_callback:
                status_callback(f"[INFO] Successfully saved {len(projects)} projects in batch. Obsolete project data was removed from dependent tables.")
        except Exception as e:
            print(f"[ERROR] Failed to save projects batch: {repr(e)}")
            raise

    def get_cost_center(self, project_id):
        """
        Fetch the cost center for a given project ID.
        :param project_id: The ID of the project to fetch the cost center for.
        :return: The cost center as a string or None if not found.
        """
        query = "SELECT cost_center FROM projects WHERE project_id = %s"
        params = (project_id,)
        results = self.execute_query(query, params, fetch=True)
        return results[0]['cost_center'] if results else None
