import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from db.base_repository import BaseRepository

class ExistingAssetDepreciationRepository(BaseRepository):
    def fetch_depreciations_by_cost_center(self, report_type='monthly'):
        """
        Fetch existing asset depreciations grouped by cost center, year, and month or year.
        """
        import pandas as pd
        import psycopg2
        from psycopg2.extras import RealDictCursor
        if report_type == 'yearly':
            group_cols = 'kustannuspaikka, tilivuosi'
            select_cols = 'kustannuspaikka as cost_center, tilivuosi as year, SUM(summa) as total_depreciation'
            query = f'''
                SELECT {select_cols}
                FROM existing_asset_depreciations
                GROUP BY {group_cols}
                ORDER BY cost_center, year
            '''
        else:
            group_cols = 'kustannuspaikka, tilivuosi, omaisuuseräjakso'
            select_cols = 'kustannuspaikka as cost_center, tilivuosi as year, omaisuuseräjakso, SUM(summa) as total_depreciation'
            query = f'''
                SELECT {select_cols}
                FROM existing_asset_depreciations
                GROUP BY {group_cols}
                ORDER BY cost_center, year, omaisuuseräjakso
            '''
        with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchall()
        df = pd.DataFrame(data)
        # If monthly, extract month from omaisuuseräjakso (last two chars, e.g. '01'-'12')
        if report_type != 'yearly' and not df.empty and 'omaisuuseräjakso' in df.columns:
            df['month'] = df['omaisuuseräjakso'].astype(str).str[-2:].astype(int)
            df = df.drop(columns=['omaisuuseräjakso'])
        return df
    def save_in_chunks(self, df, chunk_size=10000):
        """
        Save a large DataFrame to the existing asset depreciation table in chunks.
        Always cleans (truncates) the table before saving new data.
        :param df: pandas DataFrame with columns matching the table.
        :param chunk_size: Number of rows per batch insert.
        """
        columns = [
            'poistokirja', 'omaisuuseräryhmä', 'omaisuuserä', 'kuvaus', 'teksti',
            'val', 'val_summa', 'summa', 'om_erä_tapahtumapvm', 'omaisuuseräjakso',
            'tilivuosi', 'tili', 'kustannuspaikka', 'kohde'
        ]
        insert_query = f"""
            INSERT INTO existing_asset_depreciations
            ({', '.join(columns)})
            VALUES %s
        """
        truncate_query = "TRUNCATE TABLE existing_asset_depreciations"
        # Ensure DataFrame columns are lowercase for robust matching
        df.columns = [col.lower() for col in df.columns]
        try:
            data = [tuple(row[col] for col in columns) for _, row in df.iterrows()]
        except KeyError as e:
            raise KeyError(f"Column '{e.args[0]}' not found in file. Actual columns: {list(df.columns)}")
        with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cursor:
                # Clean the table before inserting new data
                cursor.execute(truncate_query)
                conn.commit()
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cursor:
                    execute_values(cursor, insert_query, chunk)
                    conn.commit()
