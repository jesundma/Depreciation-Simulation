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
        Calculate percentage-based depreciation for a project up to the year 2040.
        :param project_id: The ID of the project.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Fetch and preprocess the investment data
        df = ProjectService.get_investment_dataframe(project_id)

        # Debugging: Print the header of the DataFrame
        print("[DEBUG] DataFrame header:")
        print(df.head())

        if 'year' not in df.columns:
            print("[ERROR] 'year' column is missing from the DataFrame.")
            return

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

        # Extend the DataFrame to include years up to 2040
        last_year = df["Year"].max()
        for year in range(last_year + 1, 2041):
            df = pd.concat([df, pd.DataFrame({"Year": [year], "Investment Amount": [0.0], "Depreciation Start Year": [False]})], ignore_index=True)

        # Initialize variables
        depreciation_started = False
        remaining_asset_value = 0.0

        # Iterate through each row to calculate depreciation
        for i in range(len(df)):
            # Add new investments to the remaining asset value
            remaining_asset_value += df.loc[i, "Investment Amount"]

            # Check if depreciation should start
            if not depreciation_started and df.loc[i, "Depreciation Start Year"]:
                depreciation_started = True

            if depreciation_started:
                # Calculate depreciation for the year
                df.loc[i, "Depreciation"] = remaining_asset_value * depreciation_factor
                remaining_asset_value -= df.loc[i, "Depreciation"]

            # Update the remaining asset value for the current year
            df.loc[i, "Remaining Asset Value"] = remaining_asset_value

        # If depreciation never started, raise a warning
        if not depreciation_started:
            print("[WARNING] Depreciation never started for project. Ensure at least one row has 'Depreciation Start Year' set to True.")

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
        Calculate years-based depreciation for a project up to the year 2040.
        :param project_id: The ID of the project.
        """
        from db.database_service import DatabaseService
        db_service = DatabaseService()

        # Fetch and preprocess the investment data
        df = ProjectService.get_investment_dataframe(project_id)

        # Debugging: Print the header of the DataFrame
        print("[DEBUG] DataFrame header:")
        print(df.head())

        if 'year' not in df.columns:
            print("[ERROR] 'year' column is missing from the DataFrame.")
            return

        # Ensure the required columns are initialized
        df["Depreciation"] = 0.0
        df["Remaining Asset Value"] = 0.0

        # Query the depreciation method details for the project
        method_details = db_service.get_depreciation_method_details(project_id)
        if not method_details or "depreciation_years" not in method_details:
            raise ValueError(f"Depreciation years not found for project ID: {project_id}")

        depreciation_years = method_details["depreciation_years"]
        print(f"[DEBUG] Depreciation Years for Project {project_id}: {depreciation_years}")

        # Extend the DataFrame to include years up to 2040
        min_year, max_year = df["Year"].min(), 2040
        for year in range(min_year, max_year + 1):
            if year not in df["Year"].values:
                df = pd.concat([df, pd.DataFrame({"Year": [year], "Investment Amount": [0.0], "Depreciation Start Year": [False]})], ignore_index=True)

        # Sort the DataFrame by year
        df = df.sort_values(by="Year").reset_index(drop=True)

        # Initialize variables
        depreciation_started = False
        remaining_asset_value = 0.0
        yearly_depreciation = 0.0

        # Iterate through each row to calculate depreciation
        for i in range(len(df)):
            # Add new investments to the remaining asset value
            remaining_asset_value += df.loc[i, "Investment Amount"]

            # Check if depreciation should start
            if not depreciation_started and df.loc[i, "Depreciation Start Year"]:
                depreciation_started = True
                yearly_depreciation = remaining_asset_value / depreciation_years  # Calculate fixed yearly depreciation

            if depreciation_started:
                # Apply the fixed yearly depreciation
                df.loc[i, "Depreciation"] = yearly_depreciation
                remaining_asset_value -= yearly_depreciation

            # Update the remaining asset value for the current year
            df.loc[i, "Remaining Asset Value"] = max(remaining_asset_value, 0.0)  # Ensure it doesn't go below zero

        # If depreciation never started, raise a warning
        if not depreciation_started:
            print("[WARNING] Depreciation never started for project. Ensure at least one row has 'Depreciation Start Year' set to True.")

        # Reorder columns to place 'Depreciation' before 'Remaining Asset Value'
        df = df[["Year", "Investment Amount", "Depreciation Start Year", "Depreciation", "Remaining Asset Value"]]

        # Debug: Print the DataFrame
        print("[DEBUG] Investment DataFrame for Years Depreciation:")
        print(df)

        # Save the calculated depreciation results to the database
        db_service.save_calculated_depreciations(project_id, df)

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

        # Ensure all values in columns for years 2025 to 2035 is positive
        year_columns = [col for col in combined_df.columns if any(str(year) in col for year in range(2025, 2036))]
        combined_df[year_columns] = combined_df[year_columns].abs()

        # Save the DataFrame to an Excel file
        combined_df.to_excel(output_file, sheet_name="Depreciation Report", index=True)
        print(f"[INFO] Report saved to {output_file}")

        # Debug: Print the generated report DataFrame
        print("[DEBUG] Generated report DataFrame:")
        print(combined_df)

        return combined_df

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

