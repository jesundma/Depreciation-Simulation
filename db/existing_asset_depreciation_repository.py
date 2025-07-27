import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from db.base_repository import BaseRepository

class ExistingAssetDepreciationRepository(BaseRepository):
    def save_in_chunks(self, df, chunk_size=10000):
        """
        Save a large DataFrame to the existing asset depreciation table in chunks.
        :param df: pandas DataFrame with columns matching the table.
        :param chunk_size: Number of rows per batch insert.
        """
        columns = [
            'Poistokirja', 'Omaisuuseräryhmä', 'Omaisuuserä', 'Kuvaus', 'Teksti',
            'Val', 'Val_Summa', 'Summa', 'Om_Erä_tapahtumapvm', 'Omaisuuseräjakso',
            'Tilivuosi', 'Tili', 'Kustannuspaikka', 'Kohde'
        ]
        query = f"""
            INSERT INTO existing_asset_depreciations
            ({', '.join(columns)})
            VALUES %s
        """
        data = [tuple(row[col] for col in columns) for _, row in df.iterrows()]
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            with psycopg2.connect(self.db_url, cursor_factory=RealDictCursor) as conn:
                with conn.cursor() as cursor:
                    execute_values(cursor, query, chunk)
                    conn.commit()
