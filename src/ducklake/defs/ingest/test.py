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

# Paths
INSPECTIONS_READ_PATH = f"{GCS_BUCKET}/raw/austin/inspections/*.parquet"
ESTABLISHMENTS_READ_PATH = f"{GCS_BUCKET}/raw/austin/establishments/*.parquet"
WRITE_PATH = f"{GCS_BUCKET}/raw/austin/establishments/establishments_{int(time.time())}.parquet"


# Storage options
storage_options = {
    "aws_access_key_id": KEY_ID,
    "aws_secret_access_key": SECRET,
    "endpoint_url": "https://storage.googleapis.com"
}


# ====================================================
# Functions for Getting New Establishments to Scrape
# ====================================================
def get_all_inspection() -> pl.DataFrame:
    """
    Get all inspections.
    Args:
        None
    Returns:
        A Polars dataframe of all inspections.
    """
    with duckdb.connect('md:food_establishments') as conn:
        return conn.sql(f"""
        SELECT *
        FROM stg.stg_inspections
        WHERE inspection_date >= TODAY() - INTERVAL '1 YEAR'
        """).pl()


def get_already_scraped_establishment_ids() -> pl.Series:
    """
    Get all establishment IDs that have already been scraped.
    Args:
        None
    Returns:
        A Polars series of establishment IDs.
    """
    return (
        pl.scan_parquet('s3://' + ESTABLISHMENTS_READ_PATH, storage_options=storage_options)
        .select(pl.col('facility_id').cast(pl.Int32))
        .unique()
        .collect(engine='streaming')
        .get_column('facility_id')
    )


def get_new_establishments() -> pl.DataFrame:
    """
    Get new establishments that haven't been scraped yet.
    Args:
        all_inspection: A Polars dataframe of all inspections.
        scraped_ids: A Polars series of establishment IDs that have already been scraped.
    Returns:
        A Polars dataframe of new establishments to scrape.
    """
    # Read the existing establishments from the parquet file
    all_inspection = get_all_inspection()
    scraped_ids = get_already_scraped_establishment_ids()

    # Get new establishments that haven't been scraped yet
    new_establishments = (
        all_inspection
        .filter(~pl.col('facility_id')
        .is_in(scraped_ids))
        .unique('facility_id')
    )
    print(f'Found {new_establishments.height} new establishments to scrape')
    print(f'{new_establishments}')
    return new_establishments


if __name__ == "__main__":
    new_establishments = get_new_establishments()