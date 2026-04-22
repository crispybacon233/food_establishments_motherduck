import os
import duckdb

from dotenv import load_dotenv
load_dotenv()


def connect_ducklake():
    conn = duckdb.connect(":memory:")

    # Install/load extensions
    for ext in ["httpfs", "parquet", "ducklake", "postgres"]:
        conn.execute(f"INSTALL {ext}")
        conn.execute(f"LOAD {ext}")

    # Create the Postgres secret for DuckLake metadata
    conn.execute(f"""
    CREATE OR REPLACE SECRET pg_metadata (
        TYPE postgres,
        HOST '{os.environ["POSTGRES_HOST"]}',
        PORT {os.environ["POSTGRES_PORT"]},
        DATABASE '{os.environ["POSTGRES_DB"]}',
        USER '{os.environ["POSTGRES_USER"]}',
        PASSWORD '{os.environ["POSTGRES_PASSWORD"]}'
    )
    """)

    # Create the GCS secret for data files
    conn.execute(f"""
    CREATE OR REPLACE SECRET gcs_data (
        TYPE gcs,
        KEY_ID '{os.environ["KEY_ID"]}',
        SECRET '{os.environ["SECRET"]}'
    )
    """)

    # Attach the DuckLake catalog
    conn.execute(f"""
    ATTACH 'ducklake:postgres:'
    AS food_ducklake
    (
        META_SECRET pg_metadata,
        METADATA_SCHEMA 'ducklake',
        DATA_PATH 'gs://{os.environ["GCS_BUCKET"]}/ducklake'
    )
    """)

    # Example: inspect schemas/tables
    print(conn.execute("SHOW DATABASES").fetchall())
    
    return conn