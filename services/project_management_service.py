from db.database_service import DatabaseService
from models.project_model import Project
from typing import Optional
import json

class ProjectManagementService:
    @staticmethod
    def save_to_database(project: Project):
        """
        Save a project to the database.
        """
        db_service = DatabaseService()
        db_service.save_project(project)
    @staticmethod
    def load_from_database(project_id: str) -> Optional[Project]:
        """
        Load a project from the database.
        """
        db_service = DatabaseService()
        project_data = db_service.load_project(project_id)
        if project_data:
            # If project_data is a tuple, access by index; adjust indices as needed
            return Project(
                project_id=project_data[0],
                branch=project_data[1],
                operations=project_data[2],
                description=project_data[3],
                depreciation_method=project_data[4]
            )
        return None
    
    @staticmethod
    def search_projects(**kwargs):
        """
        Search for projects in the database based on criteria.
        Only columns defined in the Project dataclass are included in the search and results.
        """
        from models.project_model import Project
        from db.repository_factory import RepositoryFactory
        project_fields = list(Project.__dataclass_fields__.keys())
        # Filter kwargs to only include fields defined in Project
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in project_fields}
        repo = RepositoryFactory.create_project_repository()
        results = repo.search_projects(filtered_kwargs)
        # Always return all fields from the dataclass, even if missing in the row
        return [
            {field: row.get(field) for field in project_fields}
            for row in results
        ]
    
    @staticmethod
    def get_project_investments(project_id):
        """
        Fetch the investment schedule for a given project and return both investments and years.
        :param project_id: The ID of the project.
        :return: A dict with 'years' (sorted list) and 'investments' (list of dicts).
        """
        db_service = DatabaseService()
        investments = db_service.get_investment_schedule(project_id)
        # Extract all unique years from investments
        years = sorted({row['year'] for row in investments if 'year' in row and row['year'] is not None})
        return {
            'years': years,
            'investments': investments
        }
    
    @staticmethod
    def get_project_depreciations(project_id):
        """
        Placeholder: Check if calculated depreciations exist for the project.
        Returns {'has_depreciations': True/False}.
        """
        db_service = DatabaseService()
        has_depr = db_service.has_calculated_depreciations(project_id)
        return {'has_depreciations': has_depr}
    
    @staticmethod
    def save_investments_and_depreciation(project_id: str, investments: dict, depreciation_starts: dict):
        """
        Save investments and depreciation start years/months for a project.
        :param project_id: The ID of the project.
        :param investments: Dict of {year: amount}
        :param depreciation_starts: Dict of {year: (start_year, start_month)}
        """
        from db.repository_factory import RepositoryFactory
        investment_repo = RepositoryFactory.create_investment_repository()

        # Convert tickmarks or invalid year formats to integers
        investments = {int(year): amount for year, amount in investments.items() if year.isdigit() or year in ['on', 'true']}
        depreciation_starts = {
            int(year): (int(start_year) if start_year.isdigit() else None, int(start_month) if start_month.isdigit() else None)
            for year, (start_year, start_month) in depreciation_starts.items()
            if year.isdigit() or year in ['on', 'true']
        }

        # Merge investments and depreciation_starts into the required format
        merged_data = {
            year: (
                investments.get(year),
                year if depreciation_starts.get(year, (None, None))[1] is not None else None,
                depreciation_starts.get(year, (None, None))[1]
            )
            for year in set(investments.keys()).union(depreciation_starts.keys())
        }

        # Debugging: Log the adjusted merged data
        import logging
        logging.basicConfig(filename='depreciation_debug.log', level=logging.DEBUG)
        logging.debug(f"Adjusted merged data for project {project_id}: {merged_data}")

        # Save adjusted merged data
        investment_repo.save_investment_details(project_id, merged_data)
