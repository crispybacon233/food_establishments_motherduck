import os
import sys
import polars as pl
import duckdb

import gcsfs

import time

from dotenv import load_dotenv
load_dotenv()


# Environment variables
KEY_ID = os.getenv("KEY_ID")
SECRET = os.getenv("SECRET")
GCS_BUCKET = os.getenv("GCS_BUCKET")
READ_PATH = f"{GCS_BUCKET}/raw/austin/inspections/*.parquet"
WRITE_PATH = f"{GCS_BUCKET}/raw/austin/inspections/inspections_{int(time.time())}.parquet"



storage_options = {
    "aws_access_key_id": KEY_ID,
    "aws_secret_access_key": SECRET,
    "endpoint_url": "https://storage.googleapis.com"
}


def strip_coor(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Strip coordinates from the address column.
    Args:
        df: The input dataframe.
    Returns:
        The dataframe with the coordinates stripped from the address column.
    """
    return (
        lf
        .with_columns(
            pl.col("address")
            .str.replace(r"\s*\([^)]*\)$", "")
            .str.strip_chars()
            .alias("address")
        )
    )


def create_inspection_id(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Create a unique inspection ID.
    Args:
        df: The input dataframe.
    Returns:
        The dataframe with the inspection ID column.
    """
    # Concatenate the facility ID, inspection date, and process description to create a unique inspection ID.
    inspection_id = pl.col('facility_id').cast(pl.Utf8) + pl.col('inspection_date').cast(pl.Utf8) + pl.col('process_description').cast(pl.Utf8)
    return lf.with_columns(inspection_id.alias('inspection_id'))


if __name__ == "__main__":
    # ====================================================
    # Read the existing inspections from the parquet file
    # ====================================================
    existing_inspection_ids = (
        pl.scan_parquet('s3://' + READ_PATH, storage_options=storage_options)
        .pipe(strip_coor)
        .pipe(create_inspection_id)
        .select('inspection_id')
        .collect()
        .get_column('inspection_id')
    )

    # ====================================================
    # Read the latest inspections from the API
    # ====================================================
    latest_inspections = (
        pl.read_csv('https://data.austintexas.gov/resource/ecmv-9xxi.csv?$limit=50000')
        .with_columns(
            pl.col('zip_code').cast(pl.Utf8),
            pl.col('score').cast(pl.Float64),
            pl.col('inspection_date').cast(pl.Datetime).dt.date()
        )
        .lazy()
        .pipe(strip_coor)
        .pipe(create_inspection_id)
        .filter(~pl.col('inspection_id').is_in(existing_inspection_ids))
        .drop('inspection_id')
        .collect(engine='streaming')
    )

    if latest_inspections.height > 0:
        latest_inspections.write_parquet('s3://' + WRITE_PATH, storage_options=storage_options)
        print(f"Wrote {latest_inspections.height} inspections to {WRITE_PATH}")
    else:
        print("No new inspections found")


    # ====================================================
    # Create a new table view in motherduck
    # ====================================================
    conn = duckdb.connect('md:food_establishments')
    conn.execute("USE food_establishments")
    conn.execute("CREATE SCHEMA IF NOT EXISTS src")
    conn.execute(f"""
        CREATE OR REPLACE VIEW src.src_inspections AS
        SELECT * FROM read_parquet('gs://{READ_PATH}')
    """)
    conn.close()
    print('Created view inspections in motherduck')