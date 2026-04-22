-- depends_on: {{ source('dagster', 'refresh_inspections') }}

{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    merge_update_columns=[],
    unique_key=['facility_id', 'inspection_date', 'process_description'],
    schema='stg', 
    database='food_establishments',
) }}



WITH inspections AS (
    SELECT * FROM {{ source('src', 'src_inspections') }}
)


SELECT * FROM inspections
ORDER BY inspection_date DESC