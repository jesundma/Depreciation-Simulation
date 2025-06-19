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
    def search_projects(project_id=None, branch=None, operations=None, description=None):
        """
        Search for projects in the database based on criteria.
        """
        db_service = DatabaseService()
        results = db_service.search_projects(
            project_id=project_id,
            branch=branch,
            operations=operations,
            description=description
        )
        # Return a list of dicts for Flask jsonify (not a JSON string)
        return [dict(row) for row in results]
    
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
