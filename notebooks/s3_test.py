import marimo

__generated_with = "0.23.1"
app = marimo.App(width="columns")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import gcsfs
    from dotenv import load_dotenv
    import os
    load_dotenv()
    return mo, os, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The point of this notebook is to test writing dataframes directly to the s3 storage bucket on Google Cloud
    """)
    return


@app.cell
def _(os, pl):
    # load hmac creds
    storage_options = {
        "aws_access_key_id": os.getenv('KEY_ID'),
        "aws_secret_access_key": os.getenv('SECRET'),
        "endpoint_url": "https://storage.googleapis.com"
    }

    write_path = 's3://food-establishments-cnmso3jc9/inspections_old.parquet'

    # load data
    inspections_old = pl.read_parquet('data/inspections_old.parquet')

    # upload parquet to bucket
    inspections_old.write_parquet(
        write_path, 
        storage_options=storage_options
    )
    return (storage_options,)


@app.cell
def _(pl, storage_options):
    test_read = pl.read_parquet('s3://food-establishments-cnmso3jc9/raw/austin-inspections/*.parquet', storage_options=storage_options)
    return (test_read,)


@app.cell
def _(test_read):
    test_read
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
