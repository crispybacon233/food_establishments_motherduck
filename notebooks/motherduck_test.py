import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import os
    import sys
    import polars as pl
    import gcsfs
    import time
    import duckdb
    from dotenv import load_dotenv
    load_dotenv()
    return duckdb, os, time


@app.cell
def _(os, time):
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
    return KEY_ID, READ_PATH, SECRET


@app.cell
def _(duckdb):
    with duckdb.connect('md:food_establishments') as _conn:
        _conn.sql("""

        CREATE SCHEMA IF NOT EXISTS src;

        CREATE TABLE IF NOT EXISTS src.test AS
        SELECT 1;
        """)
    return


@app.cell
def _(KEY_ID, READ_PATH, SECRET, duckdb):
    connect_str = f"""
    CREATE OR REPLACE SECRET gcs_credentials (
        TYPE GCS,
        KEY_ID '{KEY_ID}',
        SECRET '{SECRET}'
    );
    """

    with duckdb.connect('md:food_establishments') as _conn:
        _conn.execute(connect_str)
        _conn.execute("CREATE SCHEMA IF NOT EXISTS src")
        _conn.execute(f"""
            CREATE OR REPLACE VIEW src.src_inspections AS
            SELECT * FROM read_parquet('gs://{READ_PATH}')
        """)
    return (connect_str,)


@app.cell
def _(connect_str, duckdb):
    with duckdb.connect('md:food_establishments') as _conn:
        _conn.execute(connect_str)
        _conn.sql("""
        SELECT * FROM src.src_inspections;
        """).show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
