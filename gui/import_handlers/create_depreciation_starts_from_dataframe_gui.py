from db.database_service import DatabaseService
import pandas as pd
from gui.status_window import StatusWindow

def create_depreciation_starts_from_dataframe_gui(filepath=None, df=None, status_callback=None):
    """
    GUI-specific handler for importing depreciation start data from an Excel file.
    Uses StatusWindow for status updates.
    """
    if df is None:
        if filepath is None:
            raise ValueError("Either 'filepath' or 'df' must be provided.")
        df = pd.read_excel(filepath)
        df.columns = [str(col).strip().lower() for col in df.columns]
    required_columns = ["project_id", "depreciation_years"]
    for col in required_columns:
        if col not in df.columns:
            msg = f"[ERROR] Missing required column: {col}"
            if status_callback:
                status_callback(msg)
            else:
                print(msg)
            return
    expanded_rows = []
    for _, row in df.iterrows():
        project_id = str(row["project_id"]).strip()
        start_year_raw = str(row["depreciation_years"]).strip()
        if not project_id or project_id.lower() == "nan" or not start_year_raw or start_year_raw.lower() == "nan":
            msg = f"[ERROR] Missing required project_id or depreciation_years in row: project_id='{project_id}', depreciation_years='{start_year_raw}'. Import aborted."
            if status_callback:
                status_callback(msg)
            else:
                print(msg)
            raise ValueError(msg)
        years = [y.strip() for y in start_year_raw.split(';') if y.strip()]
        # Handle depreciation_months with robust defaulting
        if "depreciation_months" not in df.columns or pd.isna(row["depreciation_months"]) or str(row["depreciation_months"]).strip() == "":
            months = ["1"] * len(years)
        else:
            months_raw = str(row["depreciation_months"]).strip()
            months = [m.strip() for m in months_raw.split(';') if m.strip()]
            if len(months) == len(years):
                pass  # pair by index
            elif len(months) == 1:
                months = months * len(years)
            elif len(months) < len(years):
                msg = f"[INFO] For project_id {project_id}: Number of years ({len(years)}) is greater than number of months ({len(months)}). Missing months will be filled with default value 1."
                if status_callback:
                    status_callback(msg)
                else:
                    print(msg)
                months = months + ["1"] * (len(years) - len(months))
            elif len(months) > len(years):
                msg = f"[INFO] For project_id {project_id}: Number of months ({len(months)}) is greater than number of years ({len(years)}). Extra months will be ignored."
                if status_callback:
                    status_callback(msg)
                else:
                    print(msg)
                months = months[:len(years)]
        for year, month in zip(years, months):
            if year.isdigit() and month.isdigit():
                expanded_rows.append({
                    "project_id": project_id,
                    "start_year": int(year),
                    "start_month": int(month)
                })
            else:
                msg = f"[ERROR] Non-integer year or month for project_id {project_id}: year='{year}', month='{month}'. Import aborted."
                if status_callback:
                    status_callback(msg)
                else:
                    print(msg)
                raise ValueError(msg)
    expanded_df = pd.DataFrame(expanded_rows)
    status_window = StatusWindow("Depreciation Starts Import Status")
    status_window.update_status("[INFO] Expanded depreciation starts DataFrame:")
    status_window.update_status(str(expanded_df))
    db_service = DatabaseService()
    valid_project_ids = set(db_service.get_all_project_ids())
    missing_projects = set(row["project_id"] for _, row in expanded_df.iterrows() if row["project_id"] not in valid_project_ids)
    if missing_projects:
        msg = f"[WARNING] The following project_ids are missing from the projects table and will be skipped: {sorted(missing_projects)}"
        status_window.update_status(msg)
    filtered_df = expanded_df[expanded_df["project_id"].isin(valid_project_ids)]
    depreciation_starts = [
        (row["project_id"], row["start_year"], row["start_month"]) for _, row in filtered_df.iterrows()
    ]
    if depreciation_starts:
        db_service.save_depreciation_starts_batch(depreciation_starts)
        status_window.update_status("[INFO] Depreciation starts import completed and saved to database.")
    else:
        status_window.update_status("[INFO] No valid depreciation starts to insert.")
