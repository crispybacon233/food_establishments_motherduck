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
READ_PATH = f"{GCS_BUCKET}/raw/austin/establishments/*.parquet"

storage_options = {
    "aws_access_key_id": KEY_ID,
    "aws_secret_access_key": SECRET,
    "endpoint_url": "https://storage.googleapis.com"
}



if __name__ == "__main__":
    establishments_lf = pl.scan_parquet('s3://' + READ_PATH, storage_options=storage_options)
    conn = duckdb.connect('md:food_establishments')
    conn.execute("USE food_establishments")
    conn.execute("CREATE SCHEMA IF NOT EXISTS int")
    conn.execute("DROP TABLE IF EXISTS int.int_establishments_enriched")
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS int.int_establishments_enriched AS
        SELECT * FROM read_parquet('gs://{READ_PATH}')
    """)
    conn.close()
    print('Created establishments view in motherduck source schema')