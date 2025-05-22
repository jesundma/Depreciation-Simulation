from db.database_service import DatabaseService
import pandas as pd

class CalculationService:
    @staticmethod
    def calculate_depreciation_percentage(project_id: str):
        """
        Calculate percentage-based depreciation for a project up to the year 2040.
        """
        db_service = DatabaseService()
        df = CalculationService.get_investment_dataframe(project_id)
        df.columns = df.columns.str.lower()
        # ...existing code for percentage-based depreciation...

    @staticmethod
    def calculate_depreciation_years(project_id: str):
        """
        Calculate years-based depreciation for a project up to the year 2040.
        """
        db_service = DatabaseService()
        df = CalculationService.get_investment_dataframe(project_id)
        df.columns = df.columns.str.lower()
        # ...existing code for years-based depreciation...

    @staticmethod
    def calculate_depreciation_for_all_projects():
        """
        Calculate depreciation for all projects sequentially.
        """
        db_service = DatabaseService()
        project_ids = db_service.get_all_project_ids()
        for project_id in project_ids:
            try:
                CalculationService.handle_depreciation_calculation(project_id)
            except Exception as e:
                print(f"[ERROR] Failed to calculate depreciation for project ID {project_id}: {e}")

    @staticmethod
    def handle_depreciation_calculation(project_id: str):
        """
        Handle the depreciation calculation by determining the method type and calling the appropriate function.
        """
        method_type = CalculationService.get_depreciation_method_type(project_id)
        if method_type == "percentage":
            CalculationService.calculate_depreciation_percentage(project_id)
        elif method_type == "years":
            CalculationService.calculate_depreciation_years(project_id)

    @staticmethod
    def get_depreciation_method_type(project_id: str) -> str:
        """
        Determine the type of depreciation method for the given project.
        """
        db_service = DatabaseService()
        method_details = db_service.get_depreciation_method_details(project_id)
        # Assuming method_details is a tuple: (depreciation_percentage, depreciation_years)
        if method_details is not None and len(method_details) > 0 and method_details[0] is not None:
            return "percentage"
        elif method_details is not None and len(method_details) > 1 and method_details[1] is not None:
            return "years"
        else:
            raise ValueError("Invalid depreciation method configuration.")

    @staticmethod
    def get_investment_dataframe(project_id: str) -> pd.DataFrame:
        """
        Fetch and preprocess investment data for a project.
        """
        db_service = DatabaseService()
        investment_data = db_service.get_investment_data(project_id)
        # ...existing code for preprocessing investment data...
        return pd.DataFrame(investment_data)
