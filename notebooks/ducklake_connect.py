import marimo

__generated_with = "0.23.1"
app = marimo.App(width="columns")


@app.cell
def _():
    import marimo as mo
    import duckdb
    from dotenv import load_dotenv
    import os
    load_dotenv()
    return duckdb, os


@app.cell
def _(os):
    KEY_ID = os.getenv("KEY_ID")
    SECRET = os.getenv("SECRET")
    GCS_BUCKET = os.getenv("GCS_BUCKET")



    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    return


@app.cell
def _(duckdb, os):
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
        conn.execute("USE food_ducklake")
    
        return conn

    return (connect_ducklake,)


@app.cell
def _(connect_ducklake):
    conn = connect_ducklake()
    return (conn,)


@app.cell
def _(conn):
    conn.sql("""
    select * from read_parquet('gs://food-establishments-cnmso3jc9/raw/austin/inspections/*.parquet')
    """)
    return


@app.cell
def _(conn):
    conn.sql("""
    SELECT * FROM src.src_inspections
    """).pl()
    return


@app.cell
def _(conn):
    conn.close()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
