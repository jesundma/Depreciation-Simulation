from db.database_service import DatabaseService
import pandas as pd
from tkinter import filedialog

class ImportService:
    @staticmethod
    def read_excel_to_dataframe(title: str, filetypes: list):
        """
        Common method to read an Excel file and return a DataFrame.
        :param title: Title for the file dialog.
        :param filetypes: List of file types for the file dialog.
        :return: A pandas DataFrame or None if no file is selected.
        """
        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if not file_path:
            print("[INFO] No file selected.")
            return None
        # Read the Excel file and handle mixed header types
        df = pd.read_excel(file_path, header=0)

        # Convert numeric column names to strings
        df.columns = [str(col).strip() for col in df.columns]

        return df

    @staticmethod
    def create_projects_from_dataframe(filepath=None, df=None):
        """
        Read and save project data from an Excel file to the 'projects' table.
        Accepts either a file path (filepath) or a pandas DataFrame (df).
        This function is backend-agnostic and can be used by both desktop and web frontends.
        """
        if df is None:
            if filepath is None:
                raise ValueError("Either 'filepath' or 'df' must be provided.")
            df = pd.read_excel(filepath)
        # Convert numeric column names to strings
        df.columns = [str(col).strip() for col in df.columns]
        project_columns = ["project_id", "branch", "operations", "description", "depreciation_method"]
        projects_df = df[project_columns].drop_duplicates(subset="project_id")
        projects_data = [
            (
                row["project_id"],
                row["branch"],
                row["operations"],
                row["description"],
                row["depreciation_method"]
            )
            for _, row in projects_df.iterrows()
        ]
        db_service = DatabaseService()
        db_service.save_projects_batch(projects_data)
        print("[INFO] Projects have been successfully imported and saved to the database.")

    @staticmethod
    def create_project_classifications_from_dataframe():
        """
        Read and save project classifications from an Excel file to the 'project_classifications' table.
        """
        df = ImportService.read_excel_to_dataframe(
            title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if df is None:
            return

        # Create a new DataFrame for project classifications with specific headers
        classification_columns = ["project_id", "importance", "type"]
        classifications_df = df[classification_columns].drop_duplicates(subset="project_id")

        # Convert the DataFrame to a list of tuples for batch saving
        classifications_data = [
            (
                row["project_id"],
                row["importance"],
                row["type"]
            )
            for _, row in classifications_df.iterrows()
        ]

        db_service = DatabaseService()
        db_service.save_project_classifications_batch(classifications_data)

        print("[INFO] Project classifications have been successfully imported and saved to the database.")

    @staticmethod
    def create_investments_from_dataframe():
        """
        Read and save investment data from an Excel file to the 'investments' table.
        """
        df = ImportService.read_excel_to_dataframe(
            title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if df is None:
            return
        
        # Debug: Print the column names to identify discrepancies
        print("[DEBUG] Column names in the Excel file:", df.columns.tolist())

        # Normalize column names for comparison
        df.columns = df.columns.str.strip().str.lower()
        # Convert all column names to strings after normalization
        df.columns = df.columns.map(str)
        investment_columns = [col.lower() for col in ["project_id", "2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033", "2034", "2035"]]

        # Debug: Print both investment_columns and df.columns to identify mismatches
        print("[DEBUG] Expected columns:", investment_columns)
        print("[DEBUG] Actual columns in DataFrame:", df.columns.tolist())

        # Check if all required columns are present in the DataFrame
        missing_columns = [col for col in investment_columns if col not in df.columns]
        if missing_columns:
            print(f"[ERROR] Missing required columns in the Excel file: {missing_columns}")
            return

        # Create a new DataFrame for investments with specific headers
        investment_df = df[investment_columns].drop_duplicates(subset="project_id")

        # Transform the DataFrame to unpivot yearly data into individual rows
        investment_data = [
            (row["project_id"], int(year), row[year])
            for _, row in investment_df.iterrows()
            for year in ["2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033", "2034", "2035"]
        ]

        db_service = DatabaseService()
        db_service.save_investments_batch(investment_data)

        print("[INFO] Investments have been successfully imported and saved to the database.")

    @staticmethod
    def read_depreciation_years_from_excel():
        """
        Read and save depreciation years from an Excel file to the investments table.
        """
        df = ImportService.read_excel_to_dataframe(
            title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if df is None:
            return
        db_service = DatabaseService()

    @staticmethod
    def create_depreciation_starts_from_dataframe():
        """
        Import depreciation start data from an Excel file.
        Reads a DataFrame with columns: project_id (text), start_year (semicolon-separated string of years), start_month (semicolon-separated string of months, optional).
        Each year in start_year is treated as a separate entry for the project.
        If start_month is missing, empty, or mismatched, defaults to 1.
        If both columns have equal number of values, pair them. If months has one value, use for all years. Otherwise, default all months to 1.
        """
        df = ImportService.read_excel_to_dataframe(
            title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if df is None:
            return
        # Normalize column names
        df.columns = [str(col).strip().lower() for col in df.columns]
        # Ensure required columns exist
        required_columns = ["project_id", "start_year"]
        for col in required_columns:
            if col not in df.columns:
                print(f"[ERROR] Missing required column: {col}")
                return
        expanded_rows = []
        for _, row in df.iterrows():
            project_id = str(row["project_id"])
            years = [y.strip() for y in str(row["start_year"]).split(';') if y.strip()]
            # Handle start_month: can be missing, empty, or semicolon-separated
            if "start_month" not in df.columns or pd.isna(row["start_month"]) or str(row["start_month"]).strip() == "":
                months = ["1"] * len(years)
            else:
                months_raw = str(row["start_month"]).strip()
                months = [m.strip() for m in months_raw.split(';') if m.strip()]
                if len(months) == len(years):
                    pass  # pair by index
                elif len(months) == 1:
                    months = months * len(years)
                else:
                    months = ["1"] * len(years)
            for year, month in zip(years, months):
                if year.isdigit() and month.isdigit():
                    expanded_rows.append({
                        "project_id": project_id,
                        "start_year": int(year),
                        "start_month": int(month)
                    })
        expanded_df = pd.DataFrame(expanded_rows)
        print("[INFO] Expanded depreciation starts DataFrame:")
        print(expanded_df)
        # Insert expanded_df into the appropriate database table
        db_service = DatabaseService()
        # Get all valid project_ids from the database
        valid_project_ids = set(db_service.get_all_project_ids())
        # Filter out rows with missing project_ids and warn
        missing_projects = set(row["project_id"] for _, row in expanded_df.iterrows() if row["project_id"] not in valid_project_ids)
        if missing_projects:
            print(f"[WARNING] The following project_ids are missing from the projects table and will be skipped: {sorted(missing_projects)}")
            import sys
            sys.stdout.flush()
            try:
                from gui.status_window import StatusWindow
                StatusWindow("Import Warning").update_status(f"[WARNING] The following project_ids are missing from the projects table and will be skipped: {sorted(missing_projects)}")
            except Exception as e:
                print(f"[WARNING] Could not update status window: {e}")
        filtered_df = expanded_df[expanded_df["project_id"].isin(valid_project_ids)]
        # Convert DataFrame to list of tuples (project_id, start_year, start_month)
        depreciation_starts = [
            (row["project_id"], row["start_year"], row["start_month"]) for _, row in filtered_df.iterrows()
        ]
        if depreciation_starts:
            db_service.save_depreciation_starts_batch(depreciation_starts)
            print("[INFO] Depreciation starts import completed and saved to database.")
        else:
            print("[INFO] No valid depreciation starts to insert.")
