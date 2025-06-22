import psycopg2
from psycopg2.extras import RealDictCursor
from db.base_repository import BaseRepository

class DatabaseSetupRepository(BaseRepository):
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
