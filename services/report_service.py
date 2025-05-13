from db.database_service import DatabaseService
import pandas as pd

class ReportService:
    @staticmethod
    def create_investment_depreciation_report(output_file="depreciation_report.xlsx"):
        """
        Generate a depreciation report grouped by importance, branch, and operations.
        """
        db_service = DatabaseService()
        # ...existing code for creating depreciation report...

    @staticmethod
    def group_projects_by_importance(output_file="importance_grouped_data.xlsx"):
        """
        Group projects by importance and generate a report.
        """
        db_service = DatabaseService()
        # ...existing code for grouping projects by importance...
