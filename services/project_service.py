from models.project_model import Project
from db.database_service import DatabaseService

class ProjectService:
    @staticmethod
    def save_to_database(project: Project):
        db_service = DatabaseService()
        db_service.save_project(project)

    @staticmethod
    def load_from_database(project_id: str) -> Project:
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
    def calculate_depreciation(project: Project):
        # Apply some depreciation logic
        pass

    @staticmethod
    def search_projects(project_id=None, branch=None, operations=None, description=None):
        db_service = DatabaseService()
        return db_service.search_projects(
            project_id=project_id,
            branch=branch,
            operations=operations,
            description=description
        )

    def calculate_depreciations(self, project_id):
        """
        Calculate depreciations for a given project using data from Investments and Depreciation Schedules tables.
        :param project_id: The ID of the project.
        :return: A dictionary containing calculated depreciations.
        """
        # Placeholder for logic to fetch data and calculate depreciations
        pass

def fetch_depreciation_methods():
    """
    Fetches depreciation method descriptions from the database.
    """
    try:
        from db.database_service import DatabaseService
        db_service = DatabaseService()
        query = "SELECT method_description FROM depreciation_schedules"
        results = db_service.execute_query(query, fetch=True)
        return [row['method_description'] for row in results]
    except Exception as e:
        print(f"Error fetching depreciation methods: {e}")
        return []