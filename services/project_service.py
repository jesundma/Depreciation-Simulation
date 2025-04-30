from models.project_model import Project

class ProjectService:
    @staticmethod
    def save_to_database(project: Project):
        # Logic to save project to database
        pass

    @staticmethod
    def load_from_database(project_id: str) -> Project:
        # Connect to DB and load project
        pass

    @staticmethod
    def calculate_depreciation(project: Project):
        # Apply some depreciation logic
        pass

    @staticmethod
    def search_projects(project_id=None, branch=None, operations=None, description=None):
        # Logic to search projects
        pass