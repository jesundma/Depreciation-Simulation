from db.database_service import DatabaseService
from models.project_model import Project

class ProjectManagementService:
    @staticmethod
    def save_to_database(project: Project):
        """
        Save a project to the database.
        """
        db_service = DatabaseService()
        db_service.save_project(project)

    @staticmethod
    def load_from_database(project_id: str) -> Project:
        """
        Load a project from the database.
        """
        db_service = DatabaseService()
        project_data = db_service.load_project(project_id)
        if project_data:
            return Project(
                project_id=project_data['project_id'],
                branch=project_data['branch'],
                operations=project_data['operations'],
                description=project_data['description']
            )
        return None

    @staticmethod
    def search_projects(project_id=None, branch=None, operations=None, description=None):
        """
        Search for projects in the database based on criteria.
        """
        db_service = DatabaseService()
        return db_service.search_projects(
            project_id=project_id,
            branch=branch,
            operations=operations,
            description=description
        )
