from db.repository_factory import RepositoryFactory
import pandas as pd
import logging
import os

log_path = os.path.join(os.path.dirname(__file__), '..', 'depreciation_debug.log')
# Clear the log file before writing new content
with open(log_path, 'w') as log_file:
    log_file.write('')

logger = logging.getLogger('depreciation_logger')
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(stream_handler)
logger.debug("Logger initialized and ready to write to depreciation_debug.log")

class CalculationService:
    @staticmethod
    def calculate_depreciation_percentage(project_id: str):
        """
        Calculate percentage-based depreciation for a project up to the year 2040.
        Returns the result DataFrame for debugging.
        """
        # Use repository factory to get repository instances
        investment_repo = RepositoryFactory.create_investment_repository()
        depreciation_repo = RepositoryFactory.create_depreciation_repository()

        # Get investment schedule directly from the repository
        investment_data = investment_repo.get_investment_schedule(project_id)
        logger.debug(f'investment_data: {investment_data}')  # Debug: show raw investment data
        df = pd.DataFrame(investment_data)

        # Preprocess the investment data using the preprocess_depreciation_data function
        # Pass project_id to the preprocess_depreciation_data function
        depreciation_dataframes = CalculationService.preprocess_depreciation_data(df, project_id)

        # Define depreciation percentage
        depreciation_percentage = depreciation_repo.get_depreciation_percentage(project_id)

        # Ensure compatibility between float and Decimal by converting depreciation_percentage to float and convert to monthly percentage
        depreciation_percentage = float(depreciation_percentage) / 12

        # Assume the first DataFrame corresponds to year one
        first_year_group = depreciation_dataframes[0]

        # Calculate monthly depreciation for the first year
        first_year_group.at[0, 'depreciation_base'] = first_year_group.at[0, 'investment_amount']
        depreciation_value = float(-(first_year_group.at[0, 'depreciation_base'] * depreciation_percentage) / 100)

        for i, row in first_year_group.iterrows():
            if row['investment_amount'] > 0:
                first_year_group.at[i, 'depreciation_base'] += row['investment_amount']  # Add positive investment amount to depreciation base
                depreciation_value = float(-(first_year_group.at[i, 'depreciation_base'] * depreciation_percentage) / 100)  # Recalculate monthly depreciation

            if i == first_year_group.index[0]:
                first_year_group.at[i, 'remainder'] = first_year_group.at[first_year_group.index[0], 'depreciation_base'] + depreciation_value
            else:
                first_year_group.at[i, 'remainder'] = first_year_group.at[i - 1, 'remainder'] + depreciation_value
            first_year_group.at[i, 'monthly_depreciation'] = depreciation_value

        combined_df = pd.DataFrame(columns=['year', 'month', 'investment_amount', 'depreciation_base', 'monthly_depreciation', 'remainder'])
        combined_df = pd.concat([combined_df, first_year_group], ignore_index=True)  # Append first year group

        # Calculate depreciation for subsequent years
        for idx, year_group in enumerate(depreciation_dataframes[1:], start=1):
            previous_year_group = depreciation_dataframes[idx - 1]  # Get the previous year group
            year_group.at[0, 'depreciation_base'] = previous_year_group.at[previous_year_group.index[-1], 'remainder']
            depreciation_value = float(-(year_group.at[0, 'depreciation_base'] * depreciation_percentage) / 100)

            for i, row in year_group.iterrows():
                if row['investment_amount'] < 0:
                    year_group.at[i, 'depreciation_base'] += row['investment_amount']  # Add positive investment amount to depreciation base
                    depreciation_value = float(-(year_group.at[i, 'depreciation_base'] * depreciation_percentage) / 100)  # Recalculate monthly depreciation

                if i == year_group.index[0]:
                    year_group.at[i, 'remainder'] = year_group.at[year_group.index[0], 'depreciation_base'] + depreciation_value
                else:
                    year_group.at[i, 'remainder'] = year_group.at[i - 1, 'remainder'] + depreciation_value
                year_group.at[i, 'monthly_depreciation'] = depreciation_value

            combined_df = pd.concat([combined_df, year_group], ignore_index=True)  # Append subsequent year group

        # Modify log to present all rows of the final DataFrame
        logger.debug(f"Final combined DataFrame (all rows):\n{combined_df.to_string(index=False)}")

        # Save the final DataFrame to the database
        final_columns = ['year', 'month', 'depreciation_base', 'monthly_depreciation', 'remainder', 'cost_center']
        if not set(final_columns).issubset(combined_df.columns):
            raise ValueError(f"Final DataFrame is missing required columns: {final_columns}")

        depreciation_repo.save_calculated_depreciations(project_id, combined_df[final_columns])

        return combined_df

    @staticmethod
    def calculate_depreciation_years(project_id: str):
        """
        Calculate years-based depreciation for a project up to the year 2040.
        Returns the result DataFrame for debugging (placeholder for now).
        """
        # Use repository factory to get repository instances
        investment_repo = RepositoryFactory.create_investment_repository()
        depreciation_repo = RepositoryFactory.create_depreciation_repository()

        # Get investment schedule directly from the repository
        investment_data = investment_repo.get_investment_schedule(project_id)
        logger.debug(f'investment_data: {investment_data}')  # Debug: show raw investment data
        df = pd.DataFrame(investment_data)

        # Preprocess the investment data using the preprocess_depreciation_years_data function
        # Pass project_id to the preprocess_depreciation_data function
        depreciation_dataframes = CalculationService.preprocess_depreciation_years_data(df, project_id)
        logger.debug(f'Preprocessed depreciation dataframes: {depreciation_dataframes}')  # Debug: log the preprocessed DataFrames

    @staticmethod
    def calculate_depreciation_for_all_projects():
        """
        Calculate depreciation for all projects sequentially.
        """
        # Use repository factory to get project repository
        project_repo = RepositoryFactory.create_project_repository()
        
        project_ids = project_repo.get_all_project_ids()
        for project_id in project_ids:
            try:
                CalculationService.handle_depreciation_calculation(project_id)
            except Exception as e:
                logger.error(f"Failed to calculate depreciation for project ID {project_id}: {e}")
                
    @staticmethod
    def handle_depreciation_calculation(project_id: str):
        """
        Handle the depreciation calculation by determining the method type and calling the appropriate function.
        Returns (method_type, debug_df) for debugging.
        """
        try:
            method_type = CalculationService.get_depreciation_method_type(project_id)
            logger.debug(f'Detected depreciation method type: {method_type}')
            debug_df = None
            if method_type == "percentage":
                debug_df = CalculationService.calculate_depreciation_percentage(project_id)
            elif method_type == "years":
                debug_df = CalculationService.calculate_depreciation_years(project_id)
            else:
                raise ValueError(f"Unknown depreciation method type: {method_type}")
            return method_type, debug_df
        except Exception as e:
            logger.error(f"Error in handle_depreciation_calculation: {str(e)}")
            raise  # Re-raise the exception to be handled by the caller

    @staticmethod
    def get_depreciation_method_type(project_id: str) -> str:
        """
        Determine the type of depreciation method for the given project.
        """
        # Use repository factory to get depreciation repository
        depreciation_repo = RepositoryFactory.create_depreciation_repository()
        
        method_details = depreciation_repo.get_depreciation_method_details(project_id)
        
        if method_details is None:
            raise ValueError(f"No depreciation method configured for project ID: {project_id}")
            
        # Check if percentage method is configured
        if 'depreciation_percentage' in method_details and method_details['depreciation_percentage'] is not None:
            return "percentage"
        
        # Check if years method is configured
        elif 'depreciation_years' in method_details and method_details['depreciation_years'] is not None:            
            return "years"
        
        # No valid method configured
        else:
            raise ValueError(f"Project has invalid depreciation method configuration")

    @staticmethod
    def get_investment_dataframe(project_id: str) -> pd.DataFrame:
        """
        Fetch and preprocess investment data for a project.
        """
        # Use repository factory to get investment repository
        investment_repo = RepositoryFactory.create_investment_repository()
        
        investment_data = investment_repo.get_investment_schedule(project_id)
        # ...existing code for preprocessing investment data...
        return pd.DataFrame(investment_data)

    @staticmethod
    def preprocess_depreciation_data(df, project_id):
        """
        Preprocess the input DataFrame to create the basis for depreciation DataFrames.
        Ensure investment_amount is placed in the correct month and include empty years up to 2035.
        """
        # Ensure columns are in lowercase
        df.columns = df.columns.str.lower()
        logger.debug(f'Initial DataFrame: {df}')  # Debug: log the initial DataFrame

        # Initialize variables
        depreciation_dataframes = []
        pushed_investments = 0
        current_year = None

        # Sort the DataFrame by year and month
        df = df.sort_values(by=['year', 'month'], ignore_index=True)
        logger.debug(f'Sorted DataFrame: {df}')  # Debug: log the sorted DataFrame

        # Iterate through the DataFrame
        for index, row in df.iterrows():
            year = int(row['year'])
            month = int(row['month']) if not pd.isna(row['month']) else None
            investment = float(row['investment_amount'])  # Ensure investment is a float

            logger.debug(f'Processing row {index}: year={year}, month={month}, investment={investment}')

            if not pd.isna(row['start_year']) and not pd.isna(row['month']):
                # Depreciation year and month encountered
                if current_year is None:
                    # First depreciation year and month
                    current_year = year
                    current_month = month

                    # Sum all previous investments
                    total_investment = pushed_investments + investment
                    pushed_investments = 0

                    logger.debug(f'First depreciation year: {current_year}, month: {current_month}, total_investment: {total_investment}')

                    # Create DataFrame for the first depreciation year
                    months = list(range(current_month, 13))  # Include months from start month to December
                    investment_amounts = [0] * len(months)
                    investment_amounts[0] = total_investment  # Place investment in the start month
                    depreciation_dataframes.append(
                        pd.DataFrame({'year': [current_year] * len(months), 'month': months, 'investment_amount': investment_amounts})
                    )
                else:
                    # Subsequent depreciation year and month
                    total_investment = pushed_investments + investment
                    pushed_investments = 0

                    logger.debug(f'Subsequent depreciation year: {year}, total_investment: {total_investment}')

                    # Create DataFrame for the depreciation year
                    months = list(range(1, 13))
                    investment_amounts = [0] * 12
                    investment_amounts[month - 1] = total_investment
                    depreciation_dataframes.append(
                        pd.DataFrame({'year': [year] * 12, 'month': months, 'investment_amount': investment_amounts})
                    )
            else:
                # No depreciation year and month
                if current_year is not None:
                    # Push investment to the next year
                    pushed_investments += investment
                    logger.debug(f'Pushed investment: {investment}, total pushed: {pushed_investments}')

        # Ensure all years up to 2035 are included
        all_years = set(range(df['year'].min(), 2036))
        existing_years = {int(df['year'].min())} | {int(df['year'].iloc[0]) for df in depreciation_dataframes}
        missing_years = all_years - existing_years

        for year in sorted(missing_years):
            months = list(range(1, 13))
            depreciation_dataframes.append(
                pd.DataFrame({'year': [year] * 12, 'month': months, 'investment_amount': [0] * 12})
            )

        # Sort the list of DataFrames by year in ascending order
        depreciation_dataframes.sort(key=lambda df: df['year'].iloc[0])

        # Ensure investment_amount column is of type float for all DataFrames in the list
        for df in depreciation_dataframes:
            df['investment_amount'] = df['investment_amount'].astype(float)

        # Add additional columns to every preprocessed DataFrame in the list
        for df in depreciation_dataframes:
            df['depreciation_base'] = 0
            df['monthly_depreciation'] = 0
            df['remainder'] = 0

        # Ensure all added columns are of type float for all DataFrames in the list
        for df in depreciation_dataframes:
            df['depreciation_base'] = df['depreciation_base'].astype(float)
            df['monthly_depreciation'] = df['monthly_depreciation'].astype(float)
            df['remainder'] = df['remainder'].astype(float)

        logger.debug(f'Converted added columns to float in all DataFrames: {depreciation_dataframes}')  # Debug: log the updated DataFrames

        # Fetch cost_center data for the project using the project_id
        project_repo = RepositoryFactory.create_project_repository()
        cost_center = project_repo.get_cost_center(project_id)
        logger.debug(f'Fetched cost_center: {cost_center}')  # Debug: log the cost_center

        # Add cost_center as a column to every preprocessed DataFrame in the list
        for df in depreciation_dataframes:
            df['cost_center'] = cost_center

        logger.debug(f'Added cost_center column to all DataFrames: {depreciation_dataframes}')  # Debug: log the updated DataFrames

        logger.debug(f'Ordered depreciation DataFrames: {depreciation_dataframes}')  # Debug: log the ordered DataFrames

        # Return the list of depreciation DataFrames
        return depreciation_dataframes
    
    @staticmethod
    def preprocess_depreciation_years_data(df, project_id):
        """
        Preprocess the input DataFrame to create the basis for years-based depreciation DataFrames.
        Ensure investment_amount is placed in the correct month and include empty years up to 2035.
        """
        # Ensure columns are in lowercase
        df.columns = df.columns.str.lower()
        logger.debug(f'Initial DataFrame: {df}')  # Debug: log the initial DataFrame

        depreciation_repo = RepositoryFactory.create_depreciation_repository()

        # Define depreciation years
        depreciation_years = depreciation_repo.get_depreciation_years(project_id)
        logger.debug(f'Depreciation Years: {depreciation_years}')  # Debug: log the depreciations years
