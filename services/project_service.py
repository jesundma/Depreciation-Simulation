from models.project_model import Project
from db.database_service import DatabaseService
import pandas as pd
import tkinter as tk
from tkinter import filedialog

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
        Calculate percentage-based depreciation for a project up to the year 2040.
        :param project_id: The ID of the project.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Fetch and preprocess the investment data
        df = ProjectService.get_investment_dataframe(project_id)

        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()

        # Debugging: Print the header of the DataFrame
        print("[DEBUG] DataFrame header:")
        print(df.head())

        if 'year' not in df.columns:
            print("[ERROR] 'year' column is missing from the DataFrame.")
            return

        # Ensure the required columns are initialized
        df["depreciation"] = 0.0
        df["remaining asset value"] = 0.0

        # Query the depreciation method details for the project
        method_details = db_service.get_depreciation_method_details(project_id)
        if not method_details or "depreciation_percentage" not in method_details:
            raise ValueError(f"Depreciation percentage not found for project ID: {project_id}")

        depreciation_percentage = method_details["depreciation_percentage"]
        print(f"[DEBUG] Depreciation Percentage for Project {project_id}: {depreciation_percentage}%")

        # Convert percentage to a float for calculations
        depreciation_factor = float(depreciation_percentage) / 100

        # Extend the DataFrame to include years up to 2040
        last_year = df["year"].max()
        for year in range(last_year + 1, 2041):
            df = pd.concat([df, pd.DataFrame({"year": [year], "investment amount": [0.0], "depreciation start year": [False]})], ignore_index=True)

        # Initialize variables
        depreciation_started = False
        remaining_asset_value = 0.0

        # Iterate through each row to calculate depreciation
        for i in range(len(df)):
            # Add new investments to the remaining asset value
            remaining_asset_value += df.loc[i, "investment amount"]

            # Check if depreciation should start
            if not depreciation_started and df.loc[i, "depreciation start year"]:
                depreciation_started = True

            if depreciation_started:
                # Calculate depreciation for the year
                df.loc[i, "depreciation"] = remaining_asset_value * depreciation_factor
                remaining_asset_value -= df.loc[i, "depreciation"]

            # Update the remaining asset value for the current year
            df.loc[i, "remaining asset value"] = remaining_asset_value

        # If depreciation never started, raise a warning
        if not depreciation_started:
            print("[WARNING] Depreciation never started for project. Ensure at least one row has 'Depreciation Start Year' set to True.")

        # Reorder columns to place 'Depreciation' before 'Remaining Asset Value'
        df = df[["year", "investment amount", "depreciation start year", "depreciation", "remaining asset value"]]

        # Debug: Print the DataFrame
        print("[DEBUG] Investment DataFrame for Percentage Depreciation:")
        print(df)

        # Save the calculated depreciation results to the database
        db_service.save_calculated_depreciations(project_id, df)

    @staticmethod
    def calculate_depreciation_years(project_id: str):
        """
        Calculate years-based depreciation for a project up to the year 2040.
        :param project_id: The ID of the project.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Fetch and preprocess the investment data
        df = ProjectService.get_investment_dataframe(project_id)

        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()

        # Debugging: Print the header of the DataFrame
        print("[DEBUG] DataFrame header:")
        print(df.head())

        if 'year' not in df.columns:
            print("[ERROR] 'year' column is missing from the DataFrame.")
            return

        # Ensure the required columns are initialized
        df["depreciation"] = 0.0
        df["remaining asset value"] = 0.0

        # Query the depreciation method details for the project
        method_details = db_service.get_depreciation_method_details(project_id)
        if not method_details or "depreciation_years" not in method_details:
            raise ValueError(f"Depreciation years not found for project ID: {project_id}")

        depreciation_years = method_details["depreciation_years"]
        print(f"[DEBUG] Depreciation Years for Project {project_id}: {depreciation_years}")

        # Extend the DataFrame to include years up to 2040
        min_year, max_year = df["year"].min(), 2040
        for year in range(min_year, max_year + 1):
            if year not in df["year"].values:
                df = pd.concat([df, pd.DataFrame({"year": [year], "investment amount": [0.0], "depreciation start year": [False]})], ignore_index=True)

        # Sort the DataFrame by year
        df = df.sort_values(by="year").reset_index(drop=True)

        # Initialize variables
        depreciation_started = False
        remaining_asset_value = 0.0
        yearly_depreciation = 0.0

        # Iterate through each row to calculate depreciation
        for i in range(len(df)):
            # Add new investments to the remaining asset value
            remaining_asset_value += df.loc[i, "investment amount"]

            # Check if depreciation should start
            if not depreciation_started and df.loc[i, "depreciation start year"]:
                depreciation_started = True
                yearly_depreciation = remaining_asset_value / depreciation_years  # Calculate fixed yearly depreciation

            if depreciation_started:
                # Apply the fixed yearly depreciation
                df.loc[i, "depreciation"] = yearly_depreciation
                remaining_asset_value -= yearly_depreciation

            # Update the remaining asset value for the current year
            df.loc[i, "remaining asset value"] = max(remaining_asset_value, 0.0)  # Ensure it doesn't go below zero

        # If depreciation never started, raise a warning
        if not depreciation_started:
            print("[WARNING] Depreciation never started for project. Ensure at least one row has 'Depreciation Start Year' set to True.")

        # Reorder columns to place 'Depreciation' before 'Remaining Asset Value'
        df = df[["year", "investment amount", "depreciation start year", "depreciation", "remaining asset value"]]

        # Debug: Print the DataFrame
        print("[DEBUG] Investment DataFrame for Years Depreciation:")
        print(df)

        # Save the calculated depreciation results to the database
        db_service.save_calculated_depreciations(project_id, df)

    @staticmethod
    def calculate_depreciation_for_all_projects():
        """
        Calculate depreciation for all projects sequentially.
        """
        print("[INFO] Starting depreciation calculation for all projects...")

        db_service = DatabaseService()

        # Fetch all project IDs
        project_ids = db_service.get_all_project_ids()
        print(f"[INFO] Found {len(project_ids)} projects to process.")

        for project_id in project_ids:
            try:
                print(f"[INFO] Processing project ID: {project_id}")
                ProjectService.handle_depreciation_calculation(project_id)
            except Exception as e:
                print(f"[ERROR] Failed to calculate depreciation for project ID {project_id}: {e}")

        print("[INFO] Completed depreciation calculation for all projects.")

    @staticmethod
    def create_investment_depreciation_report(output_file="depreciation_report.xlsx"):
        db_service = DatabaseService()

        # Fetch classifications and projects data from the database
        classifications = db_service.get_project_classifications()
        projects_data = pd.DataFrame(db_service.get_projects_data())

        # Convert classifications to a DataFrame
        classifications_df = pd.DataFrame(classifications)

        # Fetch classification descriptions from the database
        classification_descriptions = pd.DataFrame(db_service.execute_query("SELECT classification_id, description FROM classification_descriptions", fetch=True))

        # Merge classifications with descriptions
        classifications_df = classifications_df.merge(classification_descriptions, left_on="importance", right_on="classification_id", how="left")

        # Replace importance with description
        classifications_df.drop(columns=["importance", "classification_id"], inplace=True)
        classifications_df.rename(columns={"description": "importance"}, inplace=True)

        # Fetch depreciation data from the database
        depreciation_data = pd.DataFrame(db_service.execute_query("SELECT project_id, year, depreciation_value FROM calculated_depreciations", fetch=True))

        # Merge classifications with projects_data and depreciation_data
        merged_data = projects_data.merge(classifications_df, on="project_id", how="left")
        merged_data = merged_data.merge(depreciation_data, on="project_id", how="left")

        # Ensure depreciation_value is numeric
        merged_data["depreciation_value"] = pd.to_numeric(merged_data["depreciation_value"], errors="coerce").fillna(0)

        # Group by importance, branch, operations, and year, and calculate total depreciations
        grouped_data = merged_data.groupby(["importance", "branch", "operations", "year"]).agg(
            Total_Depreciations=("depreciation_value", "sum")
        ).reset_index()

        # Pivot the data to show years as columns
        pivoted_data = grouped_data.pivot(index=["importance", "branch", "operations"], columns="year", values="Total_Depreciations").fillna(0)

        # Save the pivoted data to an Excel file
        pivoted_data.to_excel(output_file, sheet_name="Depreciation Report", index=True)
        print(f"[INFO] Depreciation data grouped by importance (with descriptions), branch, operations, and year saved to {output_file}")

    @staticmethod
    def group_projects_by_importance(output_file="importance_grouped_data.xlsx"):
        db_service = DatabaseService()

        # Fetch classifications and projects data from the database
        classifications = db_service.get_project_classifications()
        projects_data = pd.DataFrame(db_service.get_projects_data())

        # Convert classifications to a DataFrame
        classifications_df = pd.DataFrame(classifications)

        # Fetch classification descriptions from the database
        classification_descriptions = pd.DataFrame(db_service.execute_query("SELECT classification_id, description FROM classification_descriptions", fetch=True))

        # Merge classifications with descriptions
        classifications_df = classifications_df.merge(classification_descriptions, left_on="importance", right_on="classification_id", how="left")

        # Replace importance with description
        classifications_df.drop(columns=["importance", "classification_id"], inplace=True)
        classifications_df.rename(columns={"description": "importance"}, inplace=True)

        # Fetch investments data from the database
        investments_data = pd.DataFrame(db_service.execute_query("SELECT project_id, year, investment_amount FROM investments", fetch=True))

        # Merge classifications with projects_data and investments_data
        merged_data = projects_data.merge(classifications_df, on="project_id", how="left")
        merged_data = merged_data.merge(investments_data, on="project_id", how="left")

        # Ensure investment_amount is numeric
        merged_data["investment_amount"] = pd.to_numeric(merged_data["investment_amount"], errors="coerce").fillna(0)

        # Group by importance, branch, operations, and year, and calculate total investments
        grouped_data = merged_data.groupby(["importance", "branch", "operations", "year"]).agg(
            Total_Investments=("investment_amount", "sum")
        ).reset_index()

        # Pivot the data to show years as columns
        pivoted_data = grouped_data.pivot(index=["importance", "branch", "operations"], columns="year", values="Total_Investments").fillna(0)

        # Save the pivoted data to an Excel file
        pivoted_data.to_excel(output_file, sheet_name="Grouped by Importance", index=True)
        print(f"[INFO] Grouped data by importance (with descriptions), branch, operations, and year saved to {output_file}")

    @staticmethod
    def read_projects_from_excel():
        """
        Read and save project data from an Excel file to the 'projects' table.
        """
        try:
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel Files", "*.xlsx *.xls")]
            )

            if not file_path:
                print("[INFO] No file selected.")
                return

            df = pd.read_excel(file_path)

            print("[INFO] Project data from Excel:")
            print(df)

            ProjectService.create_projects_from_dataframe(df)

        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to read project data from Excel: {e}")

    @staticmethod
    def read_project_classifications_from_excel():
        """
        Read and save project classifications from an Excel file to the 'project_classifications' table.
        """
        try:
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel Files", "*.xlsx *.xls")]
            )

            if not file_path:
                print("[INFO] No file selected.")
                return

            df = pd.read_excel(file_path)

            # Convert importance and type to integers while reading
            df["importance"] = df["importance"].fillna(0).astype(int)
            df["type"] = df["type"].fillna(0).astype(int)

            if "importance" in df.columns and "type" in df.columns:
                classifications = df[["project_id", "importance", "type"]].dropna()
                ProjectService.create_project_classifications_from_dataframe(classifications)
            else:
                print("[WARNING] 'importance' or 'type' columns not found in the Excel file.")

        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to read project classifications from Excel: {e}")

    @staticmethod
    def read_investments_from_excel():
        """
        Read and save investment data from an Excel file to the 'investments' table.
        """
        try:
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel Files", "*.xlsx *.xls")]
            )

            if not file_path:
                print("[INFO] No file selected.")
                return

            # Use the new create_dataframe_from_excel method to process the Excel file
            df = ProjectService.create_dataframe_from_excel(file_path)

            # Debugging: Print the header of the DataFrame
            print("[DEBUG] DataFrame header:")
            print(df.head())

            # Pass the processed DataFrame to create investments
            ProjectService.create_investments_from_dataframe(df)

        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to read investment data from Excel: {e}")

    @staticmethod
    def read_depreciation_years_from_excel():
        """
        Read and save depreciation years from an Excel file to the investments table.
        """
        try:
            file_path = filedialog.askopenfilename(
                title="Select Excel File",
                filetypes=[("Excel Files", "*.xlsx *.xls")]
            )

            if not file_path:
                print("[INFO] No file selected.")
                return

            df = ProjectService.create_dataframe_from_excel(file_path)

            print("[INFO] Depreciation years data from Excel:")
            print(df)

            # Use create_depreciation_years_from_dataframe instead of update_investments_with_depreciation_years
            ProjectService.create_depreciation_years_from_dataframe(df)

        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to read depreciation years from Excel: {e}")

    @staticmethod
    def update_investments_with_depreciation_years(df: pd.DataFrame):
        """
        Update the investments table with depreciation start years from a DataFrame.
        :param df: A pandas DataFrame with columns: project_id, year, depreciation_start_year.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        for _, row in df.iterrows():
            try:
                project_id = row['project_id']
                year = int(row['year'])
                depreciation_start_years = row['depreciation_start_year']

                # Ensure depreciation_start_years is a list
                if not isinstance(depreciation_start_years, list):
                    depreciation_start_years = [depreciation_start_years]

                for depreciation_start_year in depreciation_start_years:
                    # Update the investments table for each year in the list
                    db_service.update_investment_depreciation_start_year(
                        project_id=project_id,
                        year=year,
                        depreciation_start_year=depreciation_start_year
                    )
            except Exception as e:
                print(f"[WARNING] Skipping row due to error: {e}")

        print("[INFO] Depreciation start years updated successfully in the investments table.")

    @staticmethod
    def create_depreciation_years_from_dataframe(df: pd.DataFrame):
        """
        Create depreciation years in the database from a DataFrame.
        :param df: A pandas DataFrame with columns: project_id, year, depreciation_years.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Ensure project_id is treated as a string
        df['project_id'] = df['project_id'].astype(str)

        # Prepare depreciation years data for batch processing
        depreciation_years_data = []
        for _, row in df.iterrows():
            try:
                project_id = row['project_id']
                depreciation_years = row['depreciation_years']

                # Ensure depreciation_years is processed correctly
                if pd.isna(depreciation_years):
                    depreciation_years = []
                elif isinstance(depreciation_years, str):
                    depreciation_years = [int(y.strip()) for y in depreciation_years.split(';') if y.strip().isdigit()]
                elif isinstance(depreciation_years, int):
                    depreciation_years = [depreciation_years]

                for depreciation_year in depreciation_years:
                    # Add to batch data
                    depreciation_years_data.append((project_id, depreciation_year, depreciation_year))
            except Exception as e:
                print(f"[WARNING] Skipping row due to error: {e}")

        # Save depreciation years in batch
        db_service.save_depreciation_years_batch(depreciation_years_data)
        print("[INFO] Depreciation years updated successfully in the investments table.")

    @staticmethod
    def create_projects_from_dataframe(df: pd.DataFrame):
        """
        Create new projects in the database from a DataFrame in batches.
        :param df: A pandas DataFrame with columns: project_id, branch, operations, description, depreciation_method.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Deduplicate the project data by project_id
        project_data = list({row['project_id']: (
            row['project_id'],
            row['branch'],
            row['operations'],
            row['description'],
            row['depreciation_method']
        ) for _, row in df.iterrows()}.values())

        # Save projects in a single batch
        db_service.save_projects_batch(project_data)

        print("[INFO] Projects created successfully from DataFrame in batches.")

    @staticmethod
    def create_investments_from_dataframe(df: pd.DataFrame, chunk_size=100):
        """
        Create investments in the database for projects from a DataFrame in chunks.
        :param df: A pandas DataFrame with columns: project_id and yearly investment data.
        :param chunk_size: Number of rows to process in each chunk.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Strip column names to remove extra spaces
        df.columns = df.columns.str.strip()

        # Debugging: Print column names
        print("[DEBUG] DataFrame columns:", df.columns)

        # Convert year columns to numeric
        year_columns = [col for col in df.columns if col.isdigit()]
        for col in year_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Debugging: Print a sample of the year columns
        print("[DEBUG] Sample year columns:")
        print(df[year_columns].head())

        # Prepare investment data for batch processing
        investment_data = []
        for _, row in df.iterrows():
            project_id = row['project_id']
            yearly_investments = {
                int(year): float(row.get(year, 0)) for year in year_columns
            }
            for year, amount in yearly_investments.items():
                investment_data.append((project_id, year, amount))

        # Group by project_id and year to handle duplicates
        grouped_data = {}
        for project_id, year, amount in investment_data:
            if (project_id, year) in grouped_data:
                grouped_data[(project_id, year)] += amount
            else:
                grouped_data[(project_id, year)] = amount

        # Convert grouped data back to a list of tuples
        deduplicated_data = [(project_id, year, amount) for (project_id, year), amount in grouped_data.items()]

        # Ensure all chunks are processed
        total_chunks = (len(deduplicated_data) + chunk_size - 1) // chunk_size
        for i in range(total_chunks):
            chunk = deduplicated_data[i * chunk_size:(i + 1) * chunk_size]
            db_service.save_investments_batch(chunk)

        print(f"[INFO] Investments created successfully for {len(deduplicated_data)} rows in chunks of {chunk_size}.")

    @staticmethod
    def create_project_classifications_from_dataframe(df: pd.DataFrame):
        """
        Create project classifications in the database from a DataFrame.
        :param df: A pandas DataFrame with columns: project_id, importance, type.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Prepare project classifications data for batch processing
        classifications = []
        for _, row in df.iterrows():
            project_id = row["project_id"]
            importance = row["importance"]
            classification_type = row["type"]

            if isinstance(importance, int) and isinstance(classification_type, int):
                classifications.append((project_id, importance, classification_type))
            else:
                print(f"[WARNING] Skipping invalid classification for project {project_id}: Importance={importance}, Type={classification_type}")

        # Save project classifications in batch
        db_service.save_project_classifications_batch(classifications)
        print("[INFO] Project classifications saved successfully in batch.")

    @staticmethod
    def create_dataframe_from_excel(file_path: str) -> pd.DataFrame:
        """
        Create a pandas DataFrame from an Excel file with specific transformations.
        :param file_path: Path to the Excel file.
        :return: A pandas DataFrame with processed data.
        """
        # Read the Excel file into a DataFrame, specifying the header row
        df = pd.read_excel(file_path, header=0)  # Adjust header row if needed

        # Strip column names to remove extra spaces
        df.columns = df.columns.map(lambda x: str(x).strip() if not pd.isna(x) else x)

        # Debugging: Print the cleaned column names
        print("[DEBUG] Cleaned DataFrame columns:", df.columns)

        return df

