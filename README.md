# GloboRetail Analytics Pipeline

A hybrid **ETL + ELT** pipeline for retail sales analytics. Raw data lands in S3, gets
extracted/validated/transformed in Python via Airflow, is written back to S3 as
Parquet, and is then loaded and modeled entirely inside **Snowflake** (star schema +
materialized views for reporting).

## Architecture

```
S3 (raw zone)                                S3 (transformed zone)
  sales_data.csv        ┌────────────┐          sales_data.parquet
  product_data.json     │  Airflow   │          product_data.parquet
                   ────► │  (ETL)     │ ────►    merged_sales_product_data.parquet
                         └────────────┘                    │
                                                            │ COPY INTO
                                                            ▼
                                                   Snowflake (ELT)
                                          CLEANSED_LAYER ──► STAR ──► PRESENTATION_LAYER
                                          (raw-cleaned)   (star schema)  (materialized views)
```

- **ETL (Python / Airflow):** extract → validate input → transform/clean → validate
  output → write Parquet to S3. This is the only part of the pipeline that touches
  pandas dataframes.
- **ELT (Snowflake):** Airflow only tells Snowflake *which* S3 files are ready. Snowflake
  reads them straight from its own external stage via `COPY INTO`, and all further
  modeling (star schema tables, materialized views) is done with SQL running inside
  Snowflake — no dataframes cross back into Python for this part.

## Project Structure

```
dags/
    retail_etl_dag.py          # Airflow DAG orchestrating the pipeline
include/
    config.yaml                 # all S3 / Snowflake configuration
    settings.py                 # loads config.yaml into typed constants
    logger.py                   # shared logger setup
    s3_utils.py                 # S3 hook / storage_options helper
    etl/
        extract_s3.py            # discovers raw dataset paths in S3
        transform.py             # cleaning, merging, revenue calculations
        load_s3_parquet.py       # writes validated dataframes to S3 as Parquet
        load_data_to_snowflake.py# ELT load: COPY INTO from stage (no Python dataframes)
        utils.py                 # generic S3 read helpers (csv/json/parquet)
    validations/
        input_schemas.py         # Pandera schemas for raw data
        output_schemas.py        # Pandera schemas for cleaned/merged data
        validations.py           # validate_input / validate_output entry points
sql/
    setup_snowflake.txt          # ROLE, WAREHOUSE, DATABASE, SCHEMAS, STAGE, TABLES,
                                  # STAR schema, and materialized views
notebooks/
    explore_data.ipynb           # ad-hoc exploration of the sample data
requirements.txt
```

## Data Sources

Raw data is read from Amazon S3 (`regular-exam/raw-data/`):

| Dataset | Format | Description |
|---|---|---|
| `sales_data` | CSV | Sales transactions (sales_id, product_id, region, qty, price, timestamp, discount, order_status) |
| `product_data`| JSON | Product catalog (product_id, category, brand, rating, in_stock, launch_date) |

## Pipeline Steps (Airflow DAG: `etl_pipeline_dag`)

1. **`extract_raw_data`** — lists raw dataset paths in S3 (`extract_s3.py`).
2. **`transform_raw_data`** — validates each raw dataset against its Pandera input
   schema (`input_schemas.py`); validation problems are logged with the offending rows.
   Standardizes headers, cleans `sales_data`/`product_data`
   (type casting, filling missing regions, filtering invalid prices, normalizing text
   fields), validates the output against the Pandera output schema, and writes each
   cleaned dataset to S3 as Parquet (`regular-exam/transformed-data/`).
3. **`merge_data`** — joins cleaned sales and product data on `product_id`, computes
   `discount_amount` and `total_revenue`, validates the merged output, and writes
   `merged_sales_product_data.parquet` to S3.
4. **`load_to_snowflake`** — for each transformed file, runs `TRUNCATE` + `COPY INTO`
   against the corresponding `CLEANSED_LAYER` table, reading directly from the
   `PROCESSED_S3_STAGE` external stage. This is the ELT boundary: Snowflake, not
   Python, performs the load.

## Snowflake Setup (`sql/setup_snowflake.txt`)

Run once (as `ACCOUNTADMIN` / `EXAM_ETL_ROLE`) to provision:

- **Role & Warehouse:** `EXAM_ETL_ROLE`, `EXAM_ETL_WAREHOUSE`
- **Database & Schemas:** `EXAM_EX.CLEANSED_LAYER`, `EXAM_EX.STAR`, `EXAM_EX.PRESENTATION_LAYER`
- **File Format & Stage:** `PARQUET_FILE_FORMAT`, `PROCESSED_S3_STAGE`
  (points at `s3://datawarehouse-etl-softuni/regular-exam/transformed-data/`)
- **Cleansed tables:** `SALES_CLEAN`, `PRODUCT_CLEAN`, `SALES_SUMMARY` — loaded by the
  Airflow DAG's `load_to_snowflake` task via `COPY INTO`
- **Star schema (`STAR` schema):**
  - `DIM_DATE` — one row per calendar date derived from `SALES_CLEAN`
  - `DIM_PRODUCT` — product attributes from `PRODUCT_CLEAN`
  - `FACT_SALES` — sales facts (qty, price, discount, revenue) keyed by
    `SALES_ID`, `PRODUCT_ID`, `DATE_KEY`, built from `SALES_SUMMARY`
- **Materialized views (`PRESENTATION_LAYER` schema)**, each built from a single
  source table so Snowflake can maintain them automatically:
  - `MV_SALES_BY_REGION_MONTH` — quantity/revenue/discount by region and month
  - `MV_TOP_PRODUCTS_BY_REVENUE` — revenue and volume by product
  - `MV_REVENUE_TREND` — daily revenue trend
  - `MV_CATEGORY_PERFORMANCE` — quantity, average price/rating, and revenue by category

## Configuration (`include/config.yaml`)

All S3 paths and Snowflake targets are configured in one place and loaded via
`include/settings.py`:

```yaml
aws:
  conn_id: aws_conn_id
  bucket_name: datawarehouse-etl-softuni
  folders:
    raw_data: regular-exam/raw-data/
    transformed_data: regular-exam/transformed-data/

snowflake:
  conn_id: my_snowflake_conn
  database: EXAM_EX
  stage: PROCESSED_S3_STAGE
  file_format: PARQUET_FILE_FORMAT
  targets:
    sales: {schema: cleansed_layer, table: sales_clean}
    products: {schema: cleansed_layer, table: product_clean}
    sales_summary: {schema: cleansed_layer, table: sales_summary}
```

## Validation

Both stages use [Pandera](https://pandera.readthedocs.io/):

- **Input validation** (`input_schemas.py`) checks raw data straight from S3: correct
  types, non-null required fields, positive quantities/prices, discount in `[0, 1]`,
  and `order_status` restricted to known values. Failures are logged with the specific
  rows that failed.
- **Output validation** (`output_schemas.py`) re-checks the cleaned/merged data after
  transformation — enforcing final datatypes, non-negative discount/revenue amounts,
  rating in `[0, 5]`, valid region values, and title-cased category names — and raises
  if anything doesn't conform, stopping the pipeline before bad data reaches S3 or
  Snowflake.

## Running Locally

This project uses the [Astro CLI](https://www.astronomer.io/docs/astro/cli/overview):

```bash
astro dev start
```

This spins up local Airflow (Postgres, Scheduler, DAG Processor, API Server,
Triggerer) and opens the UI at `http://localhost:8080`.

### Required Airflow Connections

| Connection ID | Type | Used for |
|---|---|---|
| `aws_conn_id` | Amazon Web Services | reading/writing S3 in the ETL steps |
| `my_snowflake_conn` | Snowflake | running `COPY INTO` in the ELT step |

## Requirements

See `requirements.txt` — key libraries: `pandas`, `pandera`, `s3fs`,
`apache-airflow-providers-amazon`, `apache-airflow-providers-snowflake`,
`snowflake-connector-python`.
