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
