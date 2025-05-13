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
    def create_projects_from_dataframe():
        """
        Read and save project data from an Excel file to the 'projects' table.
        """
        df = ImportService.read_excel_to_dataframe(
            title="Select Excel File", filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if df is None:
            return
        print(df.head)
        # Create a new DataFrame for projects with specific headers
        project_columns = ["project_id", "branch", "operations", "description", "depreciation_method"]
        projects_df = df[project_columns].drop_duplicates(subset="project_id")

        # Convert the DataFrame to a list of tuples for batch saving
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
        db_service.save_project_classifications(classifications_data)

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
        # ...existing code for reading depreciation years...
