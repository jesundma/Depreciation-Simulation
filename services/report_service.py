from db.database_service import DatabaseService
import pandas as pd
import openpyxl

class ReportService:
    @staticmethod
    def create_investment_depreciation_report(output_file="depreciation_report.xlsx"):
        """
        Generate a depreciation report grouped by importance, branch, and operations.
        """
        db_service = DatabaseService()
        # ...existing code for creating depreciation report...

    @staticmethod
    def group_projects_by_importance(output_file="importance_and_type_grouped_data.xlsx"):
        """
        Group projects by importance and generate a report.
        """
        db_service = DatabaseService()
        grouped_data = db_service.fetch_grouped_project_data()
        df = pd.DataFrame(grouped_data)
        # Pivot the DataFrame to have years as columns
        df_pivot = df.pivot_table(index=['importance_description', 'type_description', 'branch', 'operations', 'project_description'],
                                  columns='year',
                                  values='total_investment',
                                  aggfunc='sum').reset_index()
        df_pivot.columns = [int(col) if isinstance(col, str) and col.isdigit() else col for col in df_pivot.columns]
        df_pivot['Row Total'] = df_pivot.iloc[:, 5:].sum(axis=1)
        df_pivot.loc['Column Total'] = df_pivot.iloc[:, 5:].sum(axis=0)
        df_pivot.loc['Column Total', 'Row Total'] = df_pivot['Row Total'].sum()
        
        # Merge cells for rows with the same importance
        df_pivot['importance_description'] = df_pivot['importance_description'].where(df_pivot['importance_description'] != df_pivot['importance_description'].shift())
        
        # Merge cells for rows with the same type
        df_pivot['type_description'] = df_pivot['type_description'].where(df_pivot['type_description'] != df_pivot['type_description'].shift())

        # Merge cells for rows with the same branch
        df_pivot['branch'] = df_pivot['branch'].where(df_pivot['branch'] != df_pivot['branch'].shift())

        # Merge cells for rows with the same operations
        df_pivot['operations'] = df_pivot['operations'].where(df_pivot['operations'] != df_pivot['operations'].shift())
        
        # Ensure year columns are integers in Excel
        for col in df_pivot.columns[5:-1]:
            if isinstance(col, int):
                df_pivot[col] = pd.to_numeric(df_pivot[col], errors='coerce')
                
        # Apply alternating row colors (blue and white) to the Excel file
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_pivot.to_excel(writer, index=False, sheet_name='Sheet1')
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # Define styles for alternating colors
            blue_fill = openpyxl.styles.PatternFill(start_color='DDEBF7', end_color='DDEBF7', fill_type='solid')
            white_fill = openpyxl.styles.PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')

            for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column), start=1):
                fill = blue_fill if row_idx % 2 == 0 else white_fill
                for cell in row:
                    cell.fill = fill

        print(f"[INFO] Grouped data with years as columns has been saved to {output_file}.")
