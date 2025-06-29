import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from db.base_repository import BaseRepository

class InvestmentRepository(BaseRepository):
    def get_investment_schedule(self, project_id):
        """
        Fetch the investment schedule for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of investments with year, amount, depreciation start year, and start month.
        """
        query = """
        SELECT 
            COALESCE(idp.start_year, i.year) AS year, 
            i.investment_amount, 
            idp.start_year AS start_year,
            idp.start_month AS month
        FROM investment_depreciation_periods idp
        FULL OUTER JOIN investments i
        ON idp.project_id = i.project_id AND idp.start_year = i.year
        WHERE idp.project_id = %s OR i.project_id = %s
        ORDER BY year
        """
        params = (project_id, project_id)
        return self.execute_query(query, params, fetch=True)

    def save_investment_details(self, project_id, investments):
        """
        Save or update investment details, including amounts, start years, and start months.
        :param project_id: The ID of the project.
        :param investments: A dictionary where the key is the year and the value is a tuple of (investment_amount, start_year, start_month).
        """
        # Save investment amounts to the investments table
        investment_query = """
            INSERT INTO investments (project_id, year, investment_amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id, year) DO UPDATE
            SET investment_amount = EXCLUDED.investment_amount;
        """

        # Delete old depreciation entries for the given project ID
        delete_query = """
            DELETE FROM investment_depreciation_periods
            WHERE project_id = %s;
        """
        self.execute_query(delete_query, (project_id,))

        # Save start years and start months to the investment_depreciation_periods table
        start_year_month_query = """
            INSERT INTO investment_depreciation_periods (project_id, start_year, start_month)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id, start_year) DO UPDATE
            SET start_month = EXCLUDED.start_month;
        """

        for year, (amount, start_year, start_month) in investments.items():
            # Save investment amount
            investment_params = (project_id, year, amount)
            self.execute_query(investment_query, investment_params)

            # Save start year and start month if provided
            if start_year is not None and start_month is not None:
                start_year_month_params = (project_id, start_year, start_month)
                self.execute_query(start_year_month_query, start_year_month_params)

    def save_investments_batch(self, investments, status_callback=None):
        """
        Save multiple investments in the database in a single batch.
        :param investments: A list of tuples (project_id, year, investment_amount).
        :param status_callback: Optional callback for status updates (for GUI or web use).
        """
        query = """
            INSERT INTO investments (project_id, year, investment_amount)
            VALUES %s
            ON CONFLICT (project_id, year) DO UPDATE
            SET investment_amount = EXCLUDED.investment_amount;
        """
        try:
            if status_callback:
                status_callback(f"[INFO] Attempting to save {len(investments)} investments in batch.")
            else:
                print(f"[INFO] Attempting to save {len(investments)} investments in batch.")

            # Extract project IDs from the incoming data
            project_ids = [str(investment[0]) for investment in investments]  # Ensure all IDs are strings

            # --- Sanitize investments ---
            sanitized_investments = [
                tuple(self.sanitize_value(v) for v in investment)
                for investment in investments
            ]
            # --- End sanitization ---

            from psycopg2.extras import execute_values
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, sanitized_investments)

                    if project_ids:
                        query_delete = """
                            DELETE FROM investment_depreciation_periods
                            WHERE project_id NOT IN %s;
                        """
                        cur.execute(query_delete, (tuple(project_ids),))
                        removed_rows = cur.rowcount
                        conn.commit()
                        msg = f"[INFO] Successfully saved {len(investments)} investments in batch and removed {removed_rows} obsolete rows."
                        if status_callback:
                            status_callback(msg)
                        else:
                            print(msg)
                    else:
                        warning = "[WARNING] No project IDs provided. Skipping deletion of obsolete rows."
                        if status_callback:
                            status_callback(warning)
                        else:
                            print(warning)
        except psycopg2.errors.ForeignKeyViolation as e:
            msg = "[ERROR] ForeignKeyViolation: Some project IDs in investments are missing in the projects table. Please run 'Import Projects' to resolve this issue."
            if status_callback:
                status_callback(msg)
            print(f"[ERROR] ForeignKeyViolation: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to save investments batch: {repr(e)}")
            if status_callback:
                status_callback(f"[ERROR] Failed to save investments batch: {repr(e)}")
            raise

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
            # Only use print for status updates (status_callback is not available here)
            try:
                # --- Sanitize depreciation_starts ---
                sanitized_starts = [
                    tuple(self.sanitize_value(v) for v in row)
                    for row in depreciation_starts
                ]
                # --- End sanitization ---
                from psycopg2.extras import execute_values
                with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                    with conn.cursor() as cur:
                        execute_values(cur, query_upsert, sanitized_starts)

                        keep_pairs = [(str(t[0]), int(t[1])) for t in depreciation_starts]
                        if keep_pairs:
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

                print(f"[INFO] Successfully saved {len(depreciation_starts)} depreciation starts in batch and removed {removed_rows} obsolete rows.")
            except Exception as e:
                print(f"[ERROR] Failed to save depreciation starts batch: {e}")
                raise
        except Exception as e:
            print(f"[ERROR] Failed to save depreciation starts batch: {e}")
            raise
