from models.project_model import Project

class ProjectService:
    @staticmethod
    def save_to_database(project: Project):
        # Connect to DB and save project
        pass

    @staticmethod
    def load_from_database(project_id: str) -> Project:
        # Connect to DB and load project
        pass

    @staticmethod
    def calculate_depreciation(project: Project):
        # Apply some depreciation logic
        pass