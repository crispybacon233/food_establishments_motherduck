import marimo

__generated_with = "0.23.1"
app = marimo.App(width="columns")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import gcsfs
    import datetime
    from dotenv import load_dotenv
    import os
    load_dotenv()
    return datetime, mo, os, pl


@app.cell
def _(os):
    # load hmac creds
    storage_options = {
        "aws_access_key_id": os.getenv('KEY_ID'),
        "aws_secret_access_key": os.getenv('SECRET'),
        "endpoint_url": "https://storage.googleapis.com"
    }
    return (storage_options,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The point of this notebook is to test writing dataframes directly to the s3 storage bucket on Google Cloud
    """)
    return


@app.cell
def _():
    # write_path = 's3://food-establishments-cnmso3jc9/inspections_old.parquet'

    # # load data
    # inspections_old = pl.read_parquet('data/inspections_old.parquet')

    # # upload parquet to bucket
    # inspections_old.write_parquet(
    #     write_path, 
    #     storage_options=storage_options
    # )
    return


@app.cell
def _(pl, storage_options):
    test_read = pl.read_parquet('s3://food-establishments-cnmso3jc9/raw/austin/inspections/*.parquet', storage_options=storage_options)
    return (test_read,)


@app.cell
def _(test_read):
    test_read.columns
    return


@app.cell
def _(datetime, pl, test_read):
    (
        test_read
        .filter(pl.col('inspection_date') >= datetime.date(2025, 1, 1))
        .select(
            pl.col('address')
            .str.to_uppercase()
            .str.split(' ')
            .list.slice(-1, -1)  
        )
        .group_by('address')
        .agg(pl.len())
        .sort(by='len', descending=True)
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Old Establishments Data
    Data previously scraped from Google about establishments
    """)
    return


@app.cell
def _(pl, storage_options):
    est_path = 's3://food-establishments-cnmso3jc9/raw/austin/establishments/*.parquet'
    old_establishments = pl.read_parquet(est_path, storage_options=storage_options)
    return (old_establishments,)


@app.cell
def _(old_establishments, pl):
    (
        old_establishments
        .filter(pl.col('state') == 'TX')
        .unique('facility_id')
        .with_columns(
            address = pl.col('address') + ' ' + pl.col('city'),
            inspection_date = pl.col('inspection_date').cast(pl.Datetime).cast(pl.Date),
            zip_code = pl.col('zip').cast(pl.Int32).cast(pl.Utf8)
        )
    )
    return


@app.cell
def _(old_establishments, pl, storage_options):
    # Write parquet of ATX establishments with preexisting scraped data
    (
        old_establishments
        .filter(pl.col('state') == 'TX')
        .unique('facility_id')
        .with_columns(
            address = pl.col('address') + ' ' + pl.col('city'),
            inspection_date = pl.col('inspection_date').cast(pl.Datetime).cast(pl.Date),
            zip_code = pl.col('zip').cast(pl.Int32).cast(pl.Utf8),
            price = pl.col('price').cast(pl.Utf8)
        )
        .select(
            'restaurant_name',
            'zip_code',
            'inspection_date',
            'score',
            'address',
            'facility_id',
            'process_description',
            'latitude',
            'longitude',
            'google_name',
            'average_rating',
            'category',
            'price',
            'n_reviews'
        )
        .write_parquet('s3://food-establishments-cnmso3jc9/raw/austin/establishments/old_establishment_data.parquet', storage_options=storage_options)
    )
    return


@app.cell
def _(old_establishments, pl):
    (
        old_establishments
        .filter(pl.col('state') == 'TX')
        .group_by('city')
        .agg(pl.len())
        .sort('len', descending=True)
        .select(pl.col('city').str.split(' ').explode())
        .group_by('city')
        .agg(pl.len())
        .sort(by='len')
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
