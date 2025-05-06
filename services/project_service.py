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

        # Ensure the required columns are initialized
        df["Depreciation"] = 0.0
        df["Remaining Asset Value"] = 0.0

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
                total_value = df.loc[i - 1, "Remaining Asset Value"] + df.loc[i, "Investment Amount"]
                df.loc[i, "Depreciation"] = total_value * depreciation_factor
                df.loc[i, "Remaining Asset Value"] = total_value - df.loc[i, "Depreciation"]

        # Reorder columns to place 'Depreciation' before 'Remaining Asset Value'
        df = df[["Year", "Investment Amount", "Depreciation Start Year", "Depreciation", "Remaining Asset Value"]]

        # Debug: Print the DataFrame
        print("[DEBUG] Investment DataFrame for Percentage Depreciation:")
        print(df)

        # Save the calculated depreciation results to the database
        db_service.save_calculated_depreciations(project_id, df)

    @staticmethod
    def calculate_depreciation_years(project_id: str):
        """
        Calculate years-based depreciation for a project.
        :param project_id: The ID of the project.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Fetch and preprocess the investment data
        df = ProjectService.get_investment_dataframe(project_id)

        # Ensure the required columns are initialized
        df["Depreciation"] = 0.0
        df["Remaining Asset Value"] = 0.0

        # Query the depreciation method details for the project
        method_details = db_service.get_depreciation_method_details(project_id)
        if not method_details or "depreciation_years" not in method_details:
            raise ValueError(f"Depreciation years not found for project ID: {project_id}")

        depreciation_years = method_details["depreciation_years"]
        print(f"[DEBUG] Depreciation Years for Project {project_id}: {depreciation_years}")

        # Split the DataFrame into individual investments based on 'Depreciation Start Year'
        investments = []
        current_investment = []
        accumulated_investment = 0.0

        for _, row in df.iterrows():
            if row["Investment Amount"] > 0:  # Skip zero-value rows
                accumulated_investment += row["Investment Amount"]
                current_investment.append(row)
            if row["Depreciation Start Year"]:
                if current_investment:  # Only add non-empty investments
                    # Create a single-row DataFrame with the accumulated investment
                    investment_df = pd.DataFrame({
                        "Year": [current_investment[0]["Year"]],
                        "Investment Amount": [accumulated_investment],
                        "Depreciation Start Year": [True],
                        "Depreciation": [0.0],
                        "Remaining Asset Value": [0.0]
                    })
                    investments.append(investment_df)
                current_investment = []
                accumulated_investment = 0.0

        # Add remaining rows as the last investment if any
        if current_investment:
            investment_df = pd.DataFrame({
                "Year": [current_investment[0]["Year"]],
                "Investment Amount": [accumulated_investment],
                "Depreciation Start Year": [False],
                "Depreciation": [0.0],
                "Remaining Asset Value": [0.0]
            })
            investments.append(investment_df)

        # Debug: Print each investment DataFrame
        for i, investment_df in enumerate(investments):
            print(f"[DEBUG] Investment DataFrame {i + 1}:")
            print(investment_df)

        # Calculate depreciation for each individual DataFrame
        for investment_df in investments:
            if not investment_df.empty:
                # Calculate depreciation amount by dividing investment by number of years
                depreciation_amount = investment_df["Investment Amount"].iloc[0] / depreciation_years
                investment_df["Depreciation"] = depreciation_amount

        # Add depreciation to new rows for the remaining years
        updated_investments = []
        for investment_df in investments:
            if not investment_df.empty:
                # Extract the base year and depreciation amount
                base_year = investment_df["Year"].iloc[0]
                depreciation_amount = investment_df["Depreciation"].iloc[0]

                # Create rows for the remaining years
                for i in range(1, depreciation_years):
                    new_row = {
                        "Year": base_year + i,
                        "Investment Amount": 0.0,
                        "Depreciation Start Year": False,
                        "Depreciation": depreciation_amount,
                        "Remaining Asset Value": 0.0
                    }
                    investment_df = pd.concat([investment_df, pd.DataFrame([new_row])], ignore_index=True)

                updated_investments.append(investment_df)

        # Debug: Print each updated investment DataFrame
        for i, investment_df in enumerate(updated_investments):
            print(f"[DEBUG] Updated Investment DataFrame {i + 1} with Depreciation Rows:")
            print(investment_df)

        # Calculate remaining asset value for each DataFrame
        for investment_df in updated_investments:
            if not investment_df.empty:
                # Calculate remaining asset value for the first row
                investment_df.loc[0, "Remaining Asset Value"] = investment_df.loc[0, "Investment Amount"] - investment_df.loc[0, "Depreciation"]

                # Calculate remaining asset value for subsequent rows
                for i in range(1, len(investment_df)):
                    investment_df.loc[i, "Remaining Asset Value"] = investment_df.loc[i - 1, "Remaining Asset Value"] - investment_df.loc[i, "Depreciation"]

        # Debug: Print each updated investment DataFrame with remaining asset value
        for i, investment_df in enumerate(updated_investments):
            print(f"[DEBUG] Updated Investment DataFrame {i + 1} with Remaining Asset Value:")
            print(investment_df)

        # Combine all individual DataFrames into a single DataFrame
        combined_df = pd.concat(updated_investments, ignore_index=True)

        # Group by year and sum investments, depreciation, and remaining asset value
        combined_df = combined_df.groupby("Year", as_index=False).agg({
            "Investment Amount": "sum",
            "Depreciation": "sum",
            "Remaining Asset Value": "sum"
        })

        # Ensure all values in the DataFrame are converted to standard Python types
        combined_df = combined_df.astype({
            "Year": int,  # Convert Year to integer
            "Depreciation": float,  # Convert Depreciation to float
            "Remaining Asset Value": float,  # Convert Remaining Asset Value to float
            "Investment Amount": float  # Convert Investment Amount to float
        })

        # Reorder columns to place 'Depreciation' before 'Remaining Asset Value'
        combined_df = combined_df[["Year", "Investment Amount", "Depreciation", "Remaining Asset Value"]]

        # Debug: Print the DataFrame with data types
        print("[DEBUG] Investment DataFrame for Years Depreciation:")
        print(combined_df)
        print("[DEBUG] Data Types:")
        print(combined_df.dtypes)

        # Save the calculated depreciation results to the database
        db_service.save_calculated_depreciations(project_id, combined_df)

    @staticmethod
    def generate_report(transform=False, last_year=None, output_file="depreciation_report.xlsx") -> pd.DataFrame:
        """
        Generate a report for all investments and depreciations across all projects.
        Always save the report to an Excel file.
        :param transform: Whether to transform the DataFrame so years are columns and project IDs are row labels.
        :param last_year: The last year to include in the report.
        :param output_file: Path to save the Excel file (default: "depreciation_report.xlsx").
        :return: A pandas DataFrame with investments and depreciations shown separately by year.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Fetch data using a method from DatabaseService
        results = db_service.get_all_depreciation_reports()

        # Preprocess results to convert Decimal values to float
        processed_results = [
            {
                "project_id": row["project_id"],
                "Year": int(row["year"]),
                "Investment Amount": float(row["investment_amount"]) if row["investment_amount"] is not None else 0.0,
                "Depreciation": float(row["depreciation_value"]) if row["depreciation_value"] is not None else 0.0,
            }
            for row in results
        ]

        # Convert processed results to a DataFrame
        report_df = pd.DataFrame(processed_results)

        # Fetch project data
        projects_df = pd.DataFrame(db_service.get_projects_data())

        # Debug: Print the fetched projects DataFrame
        print("[DEBUG] Projects DataFrame:")
        print(projects_df)

        # Merge project data into the final DataFrame
        report_df = report_df.merge(
            projects_df[['project_id', 'branch', 'operations', 'description']],
            on='project_id',
            how='left'
        )

        # Separate investments and depreciation into two DataFrames
        investments_df = report_df.pivot(index='project_id', columns='Year', values='Investment Amount')
        depreciation_df = report_df.pivot(index='project_id', columns='Year', values='Depreciation')

        # Rename columns to distinguish between investments and depreciation
        investments_df.columns = [f"Investment {col}" for col in investments_df.columns]
        depreciation_df.columns = [f"Depreciation {col}" for col in depreciation_df.columns]

        # Concatenate investments and depreciation DataFrames horizontally
        combined_df = pd.concat([investments_df, depreciation_df], axis=1)

        # Add project details (branch, operations, description) to the DataFrame
        project_details = projects_df.set_index('project_id')[['branch', 'operations', 'description']]
        combined_df = project_details.join(combined_df)

        if last_year is not None:
            # Filter columns to include only data up to the selected year
            investment_cols = [col for col in combined_df.columns if col.startswith("Investment") and int(col.split()[-1]) <= last_year]
            depreciation_cols = [col for col in combined_df.columns if col.startswith("Depreciation") and int(col.split()[-1]) <= last_year]
            combined_df = combined_df[['branch', 'operations', 'description'] + investment_cols + depreciation_cols]

        # Save the DataFrame to an Excel file
        combined_df.to_excel(output_file, sheet_name="Depreciation Report", index=True)
        print(f"[INFO] Report saved to {output_file}")

        # Debug: Print the generated report DataFrame
        print("[DEBUG] Generated report DataFrame:")
        print(combined_df)

        return combined_df

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