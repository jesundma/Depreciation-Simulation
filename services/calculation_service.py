from db.repository_factory import RepositoryFactory
import pandas as pd
import logging
import os

log_path = os.path.join(os.path.dirname(__file__), '..', 'depreciation_debug.log')
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
        df.columns = df.columns.str.lower()
        # Ensure investment_amount is numeric (int or float) before inverting
        if 'investment_amount' in df.columns:
            df['investment_amount'] = pd.to_numeric(df['investment_amount'], errors='coerce').fillna(0).astype(int) * -1
        logger.debug(f'df after inverting investment_amount: {df}')  # Debug: show DataFrame after conversion
        # Find the first valid depreciation start year and month (relaxed: only require start_year and month)
        start_row = df[df['start_year'].notnull() & df['month'].notnull()].head(1)
        if not start_row.empty:
            dep_start_year = int(start_row['start_year'].values[0])
            dep_start_month = int(start_row['month'].values[0])
        else:
            logger.warning('No valid depreciation start year/month found. No depreciation calculated.')
            return pd.DataFrame()
        # Accumulate all investments up to and including the depreciation start date
        df['year'] = df['year'].astype(int)
        df['month'] = df['month'].fillna(1).astype(int)
        investments_before_start = df[(df['year'] < dep_start_year) |
                                      ((df['year'] == dep_start_year) & (df['month'] < dep_start_month))]
        total_investment = investments_before_start['investment_amount'].sum()
        logger.debug(f'Adjusted total investment before depreciation start: {total_investment}')

        # Build a DataFrame with rows for each month from the depreciation start to 2040
        rows = []
        year = dep_start_year
        month = dep_start_month
        while year <= 2040:
            # For the first year, start from dep_start_month; for others, from 1
            start_m = month if year == dep_start_year else 1
            end_m = 12
            for m in range(start_m, end_m + 1):
                rows.append({'year': year, 'month': m})
            year += 1
        result_df = pd.DataFrame(rows)
        # Place all investments from df at or after the depreciation start to the right year and month in this dataframe
        # If any investments have missing month (originally NaN), they are now set to 1
        investments_from_start = df[(df['year'] > dep_start_year) |
                                    ((df['year'] == dep_start_year) & (df['month'] >= dep_start_month))]
        inv_grouped = investments_from_start.groupby(['year', 'month'])['investment_amount'].sum().reset_index()
        result_df = result_df.merge(inv_grouped, on=['year', 'month'], how='left')
        result_df['investment_amount'] = result_df['investment_amount'].fillna(0).astype(int)

        # Add adjusted total investment to the first depreciation month
        result_df.loc[(result_df['year'] == dep_start_year) & (result_df['month'] == dep_start_month), 'investment_amount'] += total_investment

        # Initialize columns for monthly depreciation and remainder, define depreciation percentage
        result_df['depreciation_base'] = 0
        result_df['monthly_depreciation'] = 0
        result_df['remainder'] = 0
        depreciation_percentage = depreciation_repo.get_depreciation_percentage(project_id)
        
        # Ensure compatibility between float and Decimal by converting depreciation_percentage to float and convert to monthly percentage
        depreciation_percentage = float(depreciation_percentage)/12

        # Group data by year into a list of DataFrames
        grouped_by_year = [result_df[result_df['year'] == year].copy() for year in result_df['year'].unique()]

        # Assume the first DataFrame corresponds to year one
        first_year_group = grouped_by_year[0]

        # Calculate monthly depreciation for the first year
        first_year_group.at[0, 'depreciation_base'] = first_year_group.at[0, 'investment_amount']
        depreciation_value = float(-(first_year_group.at[0, 'depreciation_base'] * depreciation_percentage) / 100)  
        
        # Correct iteration over rows using unpacking of iterrows()
        for i, row in first_year_group.iterrows():
            if i == first_year_group.index[0]:
                first_year_group.at[i, 'remainder'] = first_year_group.at[first_year_group.index[0], 'depreciation_base'] + depreciation_value
            else:
                first_year_group.at[i, 'remainder'] = first_year_group.at[i - 1, 'remainder'] + depreciation_value
            first_year_group.at[i, 'monthly_depreciation'] = depreciation_value

        combined_df = pd.DataFrame(columns=['year', 'month', 'investment_amount', 'depreciation_base', 'monthly_depreciation', 'remainder'])
        combined_df = pd.concat([combined_df, first_year_group], ignore_index=True)
        # Calculate depreciation for the subsequent years
#        CalculationService.calculate_subsequent_years_depreciation(result_df, dep_start_year, depreciation_percentage)


        # Return the combined result DataFrame
        print(combined_df)
        return combined_df

    @staticmethod
    def calculate_subsequent_years_depreciation(result_df, dep_start_year, depreciation_percentage):
        # Define subsequent_years_group to resolve the undefined variable issue
        pass
#        subsequent_years_group = pd.DataFrame()
#
#        return subsequent_years_group

    @staticmethod
    def calculate_depreciation_years(project_id: str):
        """
        Calculate years-based depreciation for a project up to the year 2040.
        Returns the result DataFrame for debugging (placeholder for now).
        """
        investment_repo = RepositoryFactory.create_investment_repository()
        depreciation_repo = RepositoryFactory.create_depreciation_repository()
        investment_data = investment_repo.get_investment_schedule(project_id)
        df = pd.DataFrame(investment_data)
        df.columns = df.columns.str.lower()
        # ...existing code for years-based depreciation...
        # For now, return the empty DataFrame for debugging
        return df

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