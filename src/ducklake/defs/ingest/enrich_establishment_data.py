import os
import sys
import polars as pl
import duckdb

import gcsfs

import re
from urllib.parse import unquote
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import time

from ducklake.utils.establishment_google_scraper import scrape_establishment

from dotenv import load_dotenv
load_dotenv()


# Environment variables
KEY_ID = os.getenv("KEY_ID")
SECRET = os.getenv("SECRET")
GCS_BUCKET = os.getenv("GCS_BUCKET")

# Paths
INSPECTIONS_READ_PATH = f"{GCS_BUCKET}/raw/austin/inspections/*.parquet"
ESTABLISHMENTS_READ_PATH = f"{GCS_BUCKET}/raw/austin/establishments/*.parquet"
WRITE_PATH = f"{GCS_BUCKET}/raw/austin/establishments"


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
    Filters out inspections that are more than 1 year 
    old to filter out closed establishments.
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


def get_already_scraped_establishment_ids() -> list[int]:
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
        .to_list()
    )


def get_new_establishments() -> list[dict]:
    """
    Get new establishments that haven't been scraped yet by comparing the 
    inspection IDs to the establishment IDs that have already been scraped.

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
        .filter(~pl.col('facility_id').is_in(scraped_ids))
        .unique('facility_id')
        .select('restaurant_name', 'zip_code', 'address', 'facility_id')
    )
    print(f'Found {new_establishments.height} new establishments to scrape')
    new_establishments = new_establishments.sort('restaurant_name').to_dicts()
    return new_establishments


if __name__ == "__main__":
    new_establishments = get_new_establishments()
    if len(new_establishments) == 0:
        print('No new establishments to scrape')
        sys.exit(0)



    scraped_data_list = []

    with sync_playwright() as pw:

        # ==================================================
        # Launch browser
        # ==================================================
        print('Launching browser...')
        browser = pw.chromium.launch(
            headless=True, 
            channel="chrome"
            )
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",)
        page = context.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})

        # ==================================================
        # This needs to first go to google maps and sit for a bit to load the page
        # otherwise google blocks loading of number of reviews, price, etc.
        # ==================================================
        print('Going to Google Maps...')
        page.goto("https://www.google.com/maps/")
        time.sleep(5)

        # ==================================================
        # Scrape the establishment information
        # ==================================================
        for establishment in new_establishments[:2]:
            print(f'Searching for the establishment: {establishment["restaurant_name"]}...')
            print(f'At address: {establishment["address"]}')
            page.goto(
                f"https://www.google.com/maps/search/{establishment['restaurant_name']} {establishment['address']}" + ' TX',
                wait_until="domcontentloaded"
            )

            print('Waiting for the page to load...')
            page.wait_for_timeout(5000)

            print(f'Scraping establishment: {establishment["restaurant_name"]}')
            scraped_data = scrape_establishment(establishment, page)
            print(f'Scraped data: {scraped_data}')
            scraped_data_list.append(scraped_data)

            if len(scraped_data_list) >= 2:
                temp_df = (
                    pl.DataFrame(scraped_data_list)
                    .with_columns(
                        pl.col('updated_at').cast(pl.Date),
                        pl.col('facility_id').cast(pl.Int64),
                        pl.col('zip_code').cast(pl.Utf8),
                        pl.col('latitude').cast(pl.Float64),
                        pl.col('longitude').cast(pl.Float64),
                        pl.col('google_name').cast(pl.Utf8),
                        pl.col('average_rating').cast(pl.Float64),
                        pl.col('category').cast(pl.Utf8),
                        pl.col('price').cast(pl.Utf8),
                        pl.col('n_reviews').cast(pl.Int64),
                    )
                )
                print('Saving temp_df to parquet file...', temp_df)
                temp_file_path = f's3://{WRITE_PATH}/establishments_{int(time.time())}.parquet'
                temp_df.write_parquet(temp_file_path, storage_options=storage_options)
                print(f'Saved {len(temp_df)} establishments to {temp_file_path}')
                scraped_data_list.clear()

        browser.close()
        print('Browser closed')

        # ==================================================
        # Save the scraped data to a parquet file
        # ==================================================