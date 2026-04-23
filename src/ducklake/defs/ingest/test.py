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


# Functions
def get_all_inspection():
    return (
        pl.read_parquet('s3://' + INSPECTIONS_READ_PATH, storage_options=storage_options)
        .select('facility_id')
        .unique()
    )

def get_already_scraped_establishment_ids():
    return (
        pl.scan_parquet('s3://' + ESTABLISHMENTS_READ_PATH, storage_options=storage_options)
        .select('facility_id')
        .unique()
        .collect(engine='streaming')
        .get_column('facility_id')
    )


if __name__ == "__main__":
    # ====================================================
    # Read the existing establishments from the parquet file
    # ====================================================
    all_inspection = get_all_inspection()
    scraped_ids = get_already_scraped_establishment_ids()
    
    new_inspections = all_inspection.filter(~pl.col('facility_id').is_in(scraped_ids))
    print(new_inspections)