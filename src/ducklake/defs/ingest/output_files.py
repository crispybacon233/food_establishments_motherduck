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
WRITE_PATH = f"{GCS_BUCKET}/output-files"


storage_options = {
    "aws_access_key_id": KEY_ID,
    "aws_secret_access_key": SECRET,
    "endpoint_url": "https://storage.googleapis.com"
}


if __name__ == "__main__":
    # Connect to the motherduck database
    conn = duckdb.connect('md:food_establishments')
    conn.execute("USE food_establishments")

    # Create ATX establishments output file
    conn.sql("SELECT * FROM int.int_establishments_enriched").write_parquet(f"gs://{WRITE_PATH}/atx_establishments.parquet")
    print('ATX establishments output file created')

    # Create ATX inspections output file
    conn.sql("SELECT * FROM stg.stg_inspections").write_parquet(f"gs://{WRITE_PATH}/atx_inspections.parquet")
    print('ATX inspections output file created')