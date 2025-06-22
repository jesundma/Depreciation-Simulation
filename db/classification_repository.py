import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from db.base_repository import BaseRepository

class ClassificationRepository(BaseRepository):
    def save_project_classifications(self, classifications):
        """
        Save or update project classifications in the database.
        :param classifications: A list of tuples (project_id, importance, type).
        """
        try:
            print(f"[INFO] Attempting to save {len(classifications)} project classifications in batch.")

            project_ids = [str(classification[0]) for classification in classifications]

            # --- Sanitize classifications ---
            sanitized_classifications = [
                tuple(self.sanitize_value(v) for v in classification)
                for classification in classifications
            ]
            # --- End sanitization ---

            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    query_upsert = """
                        INSERT INTO project_classifications (project_id, importance, type)
                        VALUES %s
                        ON CONFLICT (project_id) DO UPDATE
                        SET importance = EXCLUDED.importance,
                            type = EXCLUDED.type;
                    """
                    execute_values(cur, query_upsert, sanitized_classifications)

                    if project_ids:
                        query_delete = """
                            DELETE FROM project_classifications
                            WHERE project_id NOT IN %s;
                        """
                        cur.execute(query_delete, (tuple(project_ids),))
                    else:
                        print("[WARNING] No project IDs provided. Skipping deletion of obsolete rows.")

                    conn.commit()

            print(f"[INFO] Successfully saved {len(classifications)} project classifications in batch and removed obsolete rows.")
        except Exception as e:
            print(f"[ERROR] Failed to save project classifications batch: {repr(e)}")
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
                    # --- Sanitize classifications ---
                    sanitized_classifications = [
                        tuple(self.sanitize_value(v) for v in classification)
                        for classification in classifications
                    ]
                    # --- End sanitization ---
                    execute_values(cur, query, sanitized_classifications)

                    project_ids = [str(classification[0]) for classification in classifications]

                    if project_ids:
                        query_delete = """
                            DELETE FROM project_classifications
                            WHERE project_id NOT IN %s;
                        """
                        cur.execute(query_delete, (tuple(project_ids),))
                        removed_rows = cur.rowcount
                        conn.commit()
                        print(f"[INFO] Successfully saved {len(classifications)} classifications in batch and removed {removed_rows} obsolete rows.")
                    else:
                        print("[WARNING] No project IDs provided. Skipping deletion of obsolete rows.")

                    print(f"[DEBUG] Successfully saved {len(classifications)} project classifications in batch.")
        except psycopg2.errors.ForeignKeyViolation as e:
            if "project_classifications_project_id_fkey" in str(e):
                print("[ERROR] ForeignKeyViolation: Some project IDs in classifications are missing in the projects table. Please run 'Import Projects' to resolve this issue.")
            print(f"[ERROR] ForeignKeyViolation: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to save project classifications batch: {e}")
            raise

    def get_project_classifications(self):
        """
        Fetch all project classifications from the database.
        :return: A list of dictionaries containing project_id, importance, and type.
        """
        query = "SELECT project_id, importance, type FROM project_classifications"
        return self.execute_query(query, fetch=True)
