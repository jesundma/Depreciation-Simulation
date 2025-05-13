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
        return pd.read_excel(file_path)

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
        db_service = DatabaseService()
        db_service.clear_table("project_classifications")
        # ...existing code for reading classifications...

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
        db_service = DatabaseService()
        db_service.clear_table("investments")
        # ...existing code for reading investments...

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
