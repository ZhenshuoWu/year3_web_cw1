"""
F1 Insight API - Data Import Script
Imports Ergast F1 CSV dataset into PostgreSQL database.

Usage:
    python -m data.import_csv

Make sure your CSV files are in the data/ directory.
"""

import pandas as pd
import numpy as np
from sqlalchemy import text
from app.database import engine, Base
from app.models import *

# CSV file paths - adjust if your files are named differently
CSV_DIR = "data"
CSV_FILES = {
    "seasons": f"{CSV_DIR}/seasons.csv",
    "circuits": f"{CSV_DIR}/circuits.csv",
    "drivers": f"{CSV_DIR}/drivers.csv",
    "constructors": f"{CSV_DIR}/constructors.csv",
    "status": f"{CSV_DIR}/status.csv",
    "races": f"{CSV_DIR}/races.csv",
    "results": f"{CSV_DIR}/results.csv",
    "qualifying": f"{CSV_DIR}/qualifying.csv",
    "pit_stops": f"{CSV_DIR}/pit_stops.csv",
    "lap_times": f"{CSV_DIR}/lap_times.csv",
}

# Mapping from CSV column names to database column names
COLUMN_MAPPINGS = {
    "circuits": {
        "circuitId": "circuit_id",
        "circuitRef": "circuit_ref",
    },
    "drivers": {
        "driverId": "driver_id",
        "driverRef": "driver_ref",
    },
    "constructors": {
        "constructorId": "constructor_id",
        "constructorRef": "constructor_ref",
    },
    "status": {
        "statusId": "status_id",
    },
    "races": {
        "raceId": "race_id",
        "circuitId": "circuit_id",
    },
    "results": {
        "resultId": "result_id",
        "raceId": "race_id",
        "driverId": "driver_id",
        "constructorId": "constructor_id",
        "positionText": "position_text",
        "positionOrder": "position_order",
        "fastestLap": "fastest_lap",
        "fastestLapTime": "fastest_lap_time",
        "fastestLapSpeed": "fastest_lap_speed",
        "statusId": "status_id",
    },
    "qualifying": {
        "qualifyId": "qualify_id",
        "raceId": "race_id",
        "driverId": "driver_id",
        "constructorId": "constructor_id",
    },
    "pit_stops": {
        "raceId": "race_id",
        "driverId": "driver_id",
    },
    "lap_times": {
        "raceId": "race_id",
        "driverId": "driver_id",
    },
}


def clean_dataframe(df):
    """Replace \\N and empty strings with None."""
    df = df.replace({"\\N": None, "": None})
    return df


def import_table(table_name, csv_path, conn, column_mapping=None):
    """Import a single CSV file into the database using an existing connection."""
    print(f"  Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    df = clean_dataframe(df)

    # Rename columns if mapping exists
    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Convert column names from camelCase to snake_case for any remaining
    df.columns = [
        ''.join(['_' + c.lower() if c.isupper() else c for c in col]).lstrip('_')
        for col in df.columns
    ]

    print(f"  Importing {len(df)} rows into '{table_name}'...")
    df.to_sql(
        table_name,
        con=conn,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi"
    )
    print(f"  ✓ {table_name}: {len(df)} rows imported")


def main():
    print("=" * 60)
    print("F1 Insight API - Data Import")
    print("=" * 60)

    # Step 1: Drop and recreate F1 data tables only (preserves users table)
    print("\n[1/3] Recreating database tables...")
    f1_table_names = [
        "lap_times", "pit_stops", "qualifying", "results",
        "races", "status", "constructors", "drivers", "circuits", "seasons"
    ]
    tables_to_drop = [
        Base.metadata.tables[t] for t in f1_table_names if t in Base.metadata.tables
    ]
    Base.metadata.drop_all(bind=engine, tables=tables_to_drop)
    Base.metadata.create_all(bind=engine)
    print("  ✓ Tables created")

    # Step 2: Import data in order (respecting foreign keys), wrapped in a single transaction
    print("\n[2/3] Importing CSV data...")
    import_order = [
        "seasons", "circuits", "drivers", "constructors", "status",
        "races", "results", "qualifying", "pit_stops", "lap_times"
    ]

    try:
        with engine.begin() as conn:
            for table in import_order:
                if table in CSV_FILES:
                    import_table(
                        table,
                        CSV_FILES[table],
                        conn,
                        COLUMN_MAPPINGS.get(table)
                    )
    except Exception as e:
        print(f"\n  ✗ Import failed: {e}")
        print("  All changes have been rolled back.")
        raise SystemExit(1)

    # Step 3: Verify
    print("\n[3/3] Verifying import...")
    with engine.connect() as conn:
        for table in import_order:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table}: {count} rows")
            except Exception:
                print(f"  {table}: table not found")

    print("\n" + "=" * 60)
    print("Import complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
