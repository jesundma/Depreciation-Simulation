from db.repository_factory import RepositoryFactory
import pandas as pd

class CalculationService:
    @staticmethod
    def calculate_depreciation_percentage(project_id: str):
        """
        Calculate percentage-based depreciation for a project up to the year 2040.
        """
        # Use repository factory to get repository instances
        investment_repo = RepositoryFactory.create_investment_repository()
        depreciation_repo = RepositoryFactory.create_depreciation_repository()
        # Get investment schedule directly from the repository
        investment_data = investment_repo.get_investment_schedule(project_id)
        df = pd.DataFrame(investment_data)
        df.columns = df.columns.str.lower()
        # Use a fixed annual depreciation rate (e.g., 20%)
        annual_depreciation_rate = 0.20
        rows = []
        for _, row in df.iterrows():
            start_year = int(row['year'])
            investment = float(row['investment_amount']) if row['investment_amount'] is not None else 0.0
            value = investment
            year = start_year
            month = 1
            monthly_depr = investment * annual_depreciation_rate / 12.0
            while value > 0:
                start_value = value
                if start_value < monthly_depr:
                    depreciation = start_value
                    remainder = 0.0
                else:
                    depreciation = monthly_depr
                    remainder = start_value - depreciation
                rows.append({
                    'year': year,
                    'month': month,
                    'start_value': start_value,
                    'depreciation': depreciation,
                    'remainder': remainder
                })
                value = remainder
                month += 1
                if month > 12:
                    month = 1
                    year += 1
        result_df = pd.DataFrame(rows)
        print(result_df.head(36))  # Show first 3 years for debug
        # ...further logic for saving or returning result_df...

    @staticmethod
    def calculate_depreciation_years(project_id: str):
        """
        Calculate years-based depreciation for a project up to the year 2040.
        """
        # Use repository factory to get repository instances
        investment_repo = RepositoryFactory.create_investment_repository()
        depreciation_repo = RepositoryFactory.create_depreciation_repository()
        # Get investment schedule directly from the repository
        investment_data = investment_repo.get_investment_schedule(project_id)
        df = pd.DataFrame(investment_data)
        df.columns = df.columns.str.lower()
        # ...existing code for years-based depreciation...

    @staticmethod
    def calculate_depreciation_for_all_projects():
        """
        Calculate depreciation for all projects sequentially.
        """
        # Use repository factory to get project repository
        project_repo = RepositoryFactory.create_project_repository()
        
        project_ids = project_repo.get_all_project_ids()
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
        try:
            method_type = CalculationService.get_depreciation_method_type(project_id)
            print(f"[DEBUG] Detected depreciation method type: {method_type}")
            if method_type == "percentage":
                CalculationService.calculate_depreciation_percentage(project_id)
            elif method_type == "years":
                CalculationService.calculate_depreciation_years(project_id)
            else:
                raise ValueError(f"Unknown depreciation method type: {method_type}")
            return method_type
        except Exception as e:
            print(f"[ERROR] Error in handle_depreciation_calculation: {str(e)}")
            raise  # Re-raise the exception to be handled by the caller

    @staticmethod
    def get_depreciation_method_type(project_id: str) -> str:
        """
        Determine the type of depreciation method for the given project.
        """
        # Use repository factory to get depreciation repository
        depreciation_repo = RepositoryFactory.create_depreciation_repository()
        
        method_details = depreciation_repo.get_depreciation_method_details(project_id)
        
        if method_details is None:
            raise ValueError(f"No depreciation method configured for project ID: {project_id}")
            
        # Check if percentage method is configured
        if 'depreciation_percentage' in method_details and method_details['depreciation_percentage'] is not None:
            return "percentage"
        
        # Check if years method is configured
        elif 'depreciation_years' in method_details and method_details['depreciation_years'] is not None:            
            return "years"
        
        # No valid method configured
        else:
            raise ValueError(f"Project has invalid depreciation method configuration")

    @staticmethod
    def get_investment_dataframe(project_id: str) -> pd.DataFrame:
        """
        Fetch and preprocess investment data for a project.
        """
        # Use repository factory to get investment repository
        investment_repo = RepositoryFactory.create_investment_repository()
        
        investment_data = investment_repo.get_investment_schedule(project_id)
        # ...existing code for preprocessing investment data...
        return pd.DataFrame(investment_data)