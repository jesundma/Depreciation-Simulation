from models.project_model import Project
from db.database_service import DatabaseService
import pandas as pd

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

    @staticmethod
    def get_depreciation_method_type(project_id: str) -> str:
        """
        Determine the type of depreciation method for the given project.
        :param project_id: The ID of the project.
        :return: "percentage" if the method is percentage-based, "years" if it is years-based.
        """
        db_service = DatabaseService()
        method_details = db_service.get_depreciation_method_details(project_id)
        if method_details['depreciation_percentage'] is not None and method_details['depreciation_years'] is None:
            return "percentage"
        elif method_details['depreciation_years'] is not None:
            return "years"
        else:
            raise ValueError("Invalid depreciation method configuration.")

    @staticmethod
    def handle_depreciation_calculation(project_id: str):
        """
        Handle the depreciation calculation by determining the method type and calling the appropriate function.
        :param project_id: The ID of the project.
        """
        method_type = ProjectService.get_depreciation_method_type(project_id)
        if method_type == "percentage":
            print(f"Calculating depreciation using percentage method for project ID: {project_id}")
            ProjectService.calculate_depreciation_percentage(project_id)
        elif method_type == "years":
            print(f"Calculating depreciation using years method for project ID: {project_id}")
            ProjectService.calculate_depreciation_years(project_id)
        else:
            raise ValueError("Unknown depreciation method type.")

    @staticmethod
    def get_investment_dataframe(project_id: str) -> pd.DataFrame:
        """
        Fetch and preprocess investment data for a project.
        :param project_id: The ID of the project.
        :return: A pandas DataFrame containing the investment data.
        """
        from db.database_service import DatabaseService
        from decimal import Decimal
        db_service = DatabaseService()

        # Fetch investment data for the project using DatabaseService
        investment_data = db_service.get_investment_data(project_id)

        # Preprocess the data to handle Decimal and None values
        processed_data = [
            {
                "Year": row["year"],
                "Investment Amount": float(row["investment_amount"]) if isinstance(row["investment_amount"], Decimal) else row["investment_amount"],
                "Depreciation Start Year": True if row["depreciation_start_year"] is not None else False
            }
            for row in investment_data
        ]

        # Create and return a DataFrame from the processed data
        return pd.DataFrame(processed_data)

    @staticmethod
    def calculate_depreciation_percentage(project_id: str):
        """
        Calculate percentage-based depreciation for a project.
        :param project_id: The ID of the project.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Fetch and preprocess the investment data
        df = ProjectService.get_investment_dataframe(project_id)

        # Query the depreciation method details for the project
        method_details = db_service.get_depreciation_method_details(project_id)
        if not method_details or "depreciation_percentage" not in method_details:
            raise ValueError(f"Depreciation percentage not found for project ID: {project_id}")

        depreciation_percentage = method_details["depreciation_percentage"]
        print(f"[DEBUG] Depreciation Percentage for Project {project_id}: {depreciation_percentage}%")

        # Convert percentage to a float for calculations
        depreciation_factor = float(depreciation_percentage) / 100

        # Initialize columns for Remaining Asset Value and Depreciation
        df["Remaining Asset Value"] = 0.0
        df["Depreciation"] = 0.0

        # Flag to track when depreciation starts
        depreciation_started = False
        accumulated_investment = 0.0  # Accumulate investments before depreciation starts

        # Calculate Remaining Asset Value and Depreciation iteratively
        for i in range(len(df)):
            if not depreciation_started:
                # Accumulate investments before depreciation starts
                accumulated_investment += df.loc[i, "Investment Amount"]

                # Check if depreciation should start
                if df.loc[i, "Depreciation Start Year"]:
                    depreciation_started = True
                    # Use the accumulated investment as the initial Remaining Asset Value
                    df.loc[i, "Remaining Asset Value"] = accumulated_investment
                    # Depreciation is applied directly to the first year's Remaining Asset Value
                    df.loc[i, "Depreciation"] = df.loc[i, "Remaining Asset Value"] * depreciation_factor
                    df.loc[i, "Remaining Asset Value"] -= df.loc[i, "Depreciation"]
                else:
                    # If depreciation hasn't started, Remaining Asset Value is the accumulated investment
                    df.loc[i, "Remaining Asset Value"] = accumulated_investment
            else:
                # For subsequent years after depreciation starts
                df.loc[i, "Remaining Asset Value"] = df.loc[i - 1, "Remaining Asset Value"] * (1 - depreciation_factor)
                # Depreciation is the difference between the previous and current Remaining Asset Value
                df.loc[i, "Depreciation"] = df.loc[i - 1, "Remaining Asset Value"] - df.loc[i, "Remaining Asset Value"]

        # Debug: Print the DataFrame
        print("[DEBUG] Investment DataFrame for Percentage Depreciation:")
        print(df)

        # Placeholder for percentage-based depreciation calculation logic

    @staticmethod
    def calculate_depreciation_years(project_id: str):
        """
        Calculate years-based depreciation for a project.
        :param project_id: The ID of the project.
        """
        # Fetch and preprocess the investment data
        df = ProjectService.get_investment_dataframe(project_id)

        # Debug: Print the DataFrame
        print("[DEBUG] Investment DataFrame for Years Depreciation:")
        print(df)

        # Placeholder for years-based depreciation calculation logic

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