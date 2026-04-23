-- depends_on: {{ source('dagster', 'refresh_inspections') }}

{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    merge_update_columns=[],
    unique_key=['facility_id'],
    schema='stg', 
    database='food_establishments',
) }}



WITH ranked AS (
    SELECT
        facility_id,
        restaurant_name,
        zip_code,
        address,
        ROW_NUMBER() OVER (
            PARTITION BY facility_id
            ORDER BY inspection_date DESC
        ) AS rn
    FROM {{ source('src', 'src_inspections') }}
)

SELECT
    facility_id,
    restaurant_name,
    zip_code,
    address
FROM ranked
WHERE rn = 1