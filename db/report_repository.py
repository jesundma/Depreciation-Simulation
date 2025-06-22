from db.base_repository import BaseRepository

class ReportRepository(BaseRepository):
    def fetch_report_data(self, project_id: str):
        """
        Fetch all investments and depreciations for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of dictionaries containing year, investment amount, and depreciation value.
        """
        query = """
            SELECT start_year AS year, 
                   COALESCE(SUM(investment_amount), 0) AS investment_amount,
                   COALESCE(SUM(depreciation_value), 0) AS depreciation_value
            FROM (
                SELECT start_year AS year, investment_amount, NULL AS depreciation_value
                FROM investment_depreciation_periods
                WHERE project_id = %s
                UNION ALL
                SELECT start_year AS year, NULL AS investment_amount, depreciation_value
                FROM calculated_depreciations
                WHERE project_id = %s
            ) AS combined
            GROUP BY year
            ORDER BY year;
        """
        params = (project_id, project_id)
        return self.execute_query(query, params, fetch=True)

    def get_depreciation_report(self, project_id: str):
        """
        Fetch all investments and depreciations for a given project ID.
        :param project_id: The ID of the project.
        :return: A list of dictionaries containing year, investment amount, and depreciation value.
        """
        query = """
            SELECT year, 
                   COALESCE(SUM(investment_amount), 0) AS investment_amount,
                   COALESCE(SUM(depreciation_value), 0) AS depreciation_value
            FROM (
                SELECT year, investment_amount, NULL AS depreciation_value
                FROM investments
                WHERE project_id = %s
                UNION ALL
                SELECT year, NULL AS investment_amount, depreciation_value
                FROM calculated_depreciations
                WHERE project_id = %s
            ) AS combined
            GROUP BY year
            ORDER BY year;
        """
        params = (project_id, project_id)
        return self.execute_query(query, params, fetch=True)

    def get_all_depreciation_reports(self):
        """
        Fetch all investments and depreciations across all projects.
        :return: A list of dictionaries containing project ID, year, investment amount, and depreciation value.
        """
        query = """
            SELECT project_id, year, 
                   COALESCE(SUM(investment_amount), 0) AS investment_amount,
                   COALESCE(SUM(depreciation_value), 0) AS depreciation_value
            FROM (
                SELECT project_id, year, investment_amount, NULL AS depreciation_value
                FROM investment_depreciation_periods
                UNION ALL
                SELECT project_id, year, NULL AS investment_amount, depreciation_value
                FROM calculated_depreciations
            ) AS combined
            GROUP BY project_id, year
            ORDER BY year;
        """
        return self.execute_query(query, fetch=True)

    def fetch_grouped_project_data(self):
        """
        Fetch and group project data by importance, type, branch, operations, and year.
        :return: A list of dictionaries containing grouped project data.
        """
        query = """
            SELECT 
                pc.importance,
                pc.type,
                p.branch,
                p.operations,
                p.project_id,
                i.year,
                SUM(i.investment_amount) AS total_investment,
                cd.description AS importance_description,
                tc.description AS type_description,
                p.description AS project_description
            FROM 
                project_classfifications pc
            JOIN 
                projects p ON pc.project_id = p.project_id
            JOIN 
                investments i ON p.project_id = i.project_id
            LEFT JOIN 
                classification_descriptions cd ON pc.importance = cd.classification_id
            LEFT JOIN 
                type_classification tc ON pc.type = tc.type_id
            GROUP BY 
                pc.importance, pc.type, p.branch, p.operations, p.project_id, i.year, cd.description, tc.description, p.description
            ORDER BY 
                pc.importance, pc.type, p.branch, p.operations, p.project_id, i.year;
        """
        return self.execute_query(query, fetch=True)
