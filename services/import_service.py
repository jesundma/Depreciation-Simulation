from db.database_service import DatabaseService
import pandas as pd
from tkinter import filedialog
from models.project_model import Project

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
        # Always read project_id as string (object)
        df = pd.read_excel(file_path, header=0, dtype={"project_id": str})

        # Convert numeric column names to strings
        df.columns = [str(col).strip() for col in df.columns]

        return df

    @staticmethod
    def create_projects_from_dataframe(filepath=None, df=None, status_callback=None):
        """
        Read and save project data from an Excel file to the 'projects' table.
        Accepts either a file path (filepath) or a pandas DataFrame (df).
        This function is backend-agnostic and can be used by both desktop and web frontends.
        :param status_callback: Optional function to receive status messages (for web or GUI feedback).
        """
        if df is None:
            if filepath is None:
                raise ValueError("Either 'filepath' or 'df' must be provided.")
            # Always read project_id as string (object)
            df = pd.read_excel(filepath, dtype={"project_id": str})
        # Debug: Print DataFrame dtypes and head for troubleshooting
        print("[DEBUG] DataFrame dtypes before DB insert:\n", df.dtypes)
        print("[DEBUG] DataFrame head:\n", df.head())
        # Ensure project_id is string, depreciation_method is int (if not null), others as needed
        df["project_id"] = df["project_id"].astype(str)
        if "depreciation_method" in df.columns:
            df["depreciation_method"] = pd.to_numeric(df["depreciation_method"], errors="coerce").astype('Int64')

        # Use Project dataclass fields for columns
        project_columns = [field for field in Project.__dataclass_fields__]
        projects_df = df[project_columns].drop_duplicates(subset="project_id")
        projects_data = [
            tuple(row[col] for col in project_columns)
            for _, row in projects_df.iterrows()
        ]
        db_service = DatabaseService()
        try:
            db_service.save_projects_batch(projects_data, status_callback=status_callback)
            if status_callback:
                status_callback("[INFO] Projects have been successfully imported and saved to the database.")
            else:
                print("[INFO] Projects have been successfully imported and saved to the database.")
        except Exception as e:
            if status_callback:
                status_callback(f"[ERROR] Failed to import projects: {e}")
            else:
                print(f"[ERROR] Failed to import projects: {e}")

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
    def create_investments_from_dataframe(filepath=None, df=None, status_callback=None):
        """
        Read and save investment data from an Excel file to the 'investments' table.
        Accepts either a filepath or a DataFrame. Uses status_callback for status updates if provided.
        """
        import pandas as pd
        if filepath is not None:
            try:
                df = pd.read_excel(filepath)
                # Ensure all column names are strings immediately after loading
                df.columns = [str(col).strip() for col in df.columns]
                if status_callback:
                    status_callback(f"[INFO] Loaded Excel file: {filepath}")
            except Exception as e:
                if status_callback:
                    status_callback(f"[ERROR] Failed to read Excel file: {e}")
                else:
                    print(f"[ERROR] Failed to read Excel file: {e}")
                return
        elif df is None:
            # GUI usage: open file dialog
            df = ImportService.read_excel_to_dataframe(
                title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
            )
            if df is None:
                return
        # Debug: Print the column names to identify discrepancies
        print("[DEBUG] Column names in the Excel file:", df.columns.tolist())
        # Normalize column names for comparison (lowercase, but do not convert to string again)
        df.columns = [col.strip().lower() for col in df.columns]
        investment_columns = [col.lower() for col in ["project_id", "2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033", "2034", "2035"]]
        print("[DEBUG] Expected columns:", investment_columns)
        print("[DEBUG] Actual columns in DataFrame:", df.columns.tolist())
        # Check if all required columns are present in the DataFrame
        missing_columns = [col for col in investment_columns if col not in df.columns]
        if missing_columns:
            msg = f"[ERROR] Missing required columns in the Excel file: {missing_columns}"
            if status_callback:
                status_callback(msg)
            else:
                print(msg)
            return
        # Create a new DataFrame for investments with specific headers
        investment_df = df[investment_columns].drop_duplicates(subset="project_id")
        # Transform the DataFrame to unpivot yearly data into individual rows
        investment_data = []
        for _, row in investment_df.iterrows():
            for year in investment_columns[1:]:  # skip 'project_id'
                value = row[year]
                if pd.notna(value):
                    investment_data.append((str(row["project_id"]), int(year), value))
        db_service = DatabaseService()
        try:
            db_service.save_investments_batch(investment_data, status_callback=status_callback)
            if status_callback:
                status_callback("[INFO] Investments have been successfully imported and saved to the database.")
            else:
                print("[INFO] Investments have been successfully imported and saved to the database.")
        except Exception as e:
            msg = f"[ERROR] Failed to save investments: {e}"
            if status_callback:
                status_callback(msg)
            else:
                print(msg)

    @staticmethod
    def create_depreciation_starts_from_dataframe(filepath=None, df=None, status_callback=None):
        """
        Import depreciation start data from an Excel file.
        Reads a DataFrame with columns: project_id (text), start_year (semicolon-separated string of years), start_month (semicolon-separated string of months, optional).
        Each year in start_year is treated as a separate entry for the project.
        If start_month is missing, empty, or mismatched, defaults to 1.
        If both columns have equal number of values, pair them. If months has one value, use for all years. Otherwise, default all months to 1.
        :param status_callback: Optional function to receive status messages (for web or GUI feedback).
        """
        import pandas as pd
        if df is None:
            if filepath is None:
                # GUI usage: open file dialog
                df = ImportService.read_excel_to_dataframe(
                    title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
                )
                if df is None:
                    return
            else:
                try:
                    df = pd.read_excel(filepath)
                    df.columns = [str(col).strip() for col in df.columns]
                    if status_callback:
                        status_callback(f"[INFO] Loaded Excel file: {filepath}")
                except Exception as e:
                    if status_callback:
                        status_callback(f"[ERROR] Failed to read Excel file: {e}")
                    else:
                        print(f"[ERROR] Failed to read Excel file: {e}")
                    return
        # Normalize column names
        df.columns = [str(col).strip().lower() for col in df.columns]
        # Use new column names
        required_columns = ["project_id", "depreciation_years"]
        for col in required_columns:
            if col not in df.columns:
                msg = f"[ERROR] Missing required column: {col}"
                if status_callback:
                    status_callback(msg)
                else:
                    print(msg)
                return
        expanded_rows = []
        for _, row in df.iterrows():
            project_id = str(row["project_id"]).strip()
            start_year_raw = str(row["depreciation_years"]).strip()
            if not project_id or project_id.lower() == "nan" or not start_year_raw or start_year_raw.lower() == "nan":
                msg = f"[ERROR] Missing required project_id or depreciation_years in row: project_id='{project_id}', depreciation_years='{start_year_raw}'. Import aborted."
                if status_callback:
                    status_callback(msg)
                else:
                    print(msg)
                raise ValueError(msg)
            years = [y.strip() for y in start_year_raw.split(';') if y.strip()]
            # Handle depreciation_months with robust defaulting
            if "depreciation_months" not in df.columns or pd.isna(row["depreciation_months"]) or str(row["depreciation_months"]).strip() == "":
                months = ["1"] * len(years)
            else:
                months_raw = str(row["depreciation_months"]).strip()
                months = [m.strip() for m in months_raw.split(';') if m.strip()]
                if len(months) == len(years):
                    pass  # pair by index
                elif len(months) == 1:
                    months = months * len(years)
                elif len(months) < len(years):
                    msg = f"[INFO] For project_id {project_id}: Number of years ({len(years)}) is greater than number of months ({len(months)}). Missing months will be filled with default value 1."
                    if status_callback:
                        status_callback(msg)
                    else:
                        print(msg)
                    months = months + ["1"] * (len(years) - len(months))
                elif len(months) > len(years):
                    msg = f"[INFO] For project_id {project_id}: Number of months ({len(months)}) is greater than number of years ({len(years)}). Extra months will be ignored."
                    if status_callback:
                        status_callback(msg)
                    else:
                        print(msg)
                    months = months[:len(years)]
            for year, month in zip(years, months):
                if year.isdigit() and month.isdigit():
                    expanded_rows.append({
                        "project_id": project_id,
                        "start_year": int(year),
                        "start_month": int(month)
                    })
                else:
                    msg = f"[ERROR] Non-integer year or month for project_id {project_id}: year='{year}', month='{month}'. Import aborted."
                    if status_callback:
                        status_callback(msg)
                    else:
                        print(msg)
                    raise ValueError(msg)
        expanded_df = pd.DataFrame(expanded_rows)
        if status_callback:
            status_callback("[INFO] Expanded depreciation starts DataFrame:")
            status_callback(str(expanded_df))
        else:
            print("[INFO] Expanded depreciation starts DataFrame:")
            print(expanded_df)
        db_service = DatabaseService()
        valid_project_ids = set(db_service.get_all_project_ids())
        missing_projects = set(row["project_id"] for _, row in expanded_df.iterrows() if row["project_id"] not in valid_project_ids)
        if missing_projects:
            msg = f"[WARNING] The following project_ids are missing from the projects table and will be skipped: {sorted(missing_projects)}"
            if status_callback:
                status_callback(msg)
            else:
                print(msg)
        filtered_df = expanded_df[expanded_df["project_id"].isin(valid_project_ids)]
        print("[DEBUG] expanded_df columns:", expanded_df.columns.tolist())
        print("[DEBUG] expanded_df head:\n", expanded_df.head())
        print("[DEBUG] valid_project_ids:", valid_project_ids)
        print("[DEBUG] missing_projects:", missing_projects)
        print("[DEBUG] filtered_df columns:", filtered_df.columns.tolist())
        print("[DEBUG] filtered_df head:\n", filtered_df.head())
        depreciation_starts = [
            (row["project_id"], row["start_year"], row["start_month"]) for _, row in filtered_df.iterrows()
        ]
        print("[DEBUG] depreciation_starts sample:", depreciation_starts[:5])
        if depreciation_starts:
            db_service.save_depreciation_starts_batch(depreciation_starts)
            msg = "[INFO] Depreciation starts import completed and saved to database."
            if status_callback:
                status_callback(msg)
            else:
                print(msg)
        else:
            msg = "[INFO] No valid depreciation starts to insert."
            if status_callback:
                status_callback(msg)
            else:
                print(msg)
