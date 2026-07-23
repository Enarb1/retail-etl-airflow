from airflow.sdk import task, dag
from pendulum import datetime

from include.etl.extract_s3 import extract_raw_data_paths_from_s3
from include.etl.transform import clean_data, merge_sales_and_product_data
from include.settings import (AWS_CONN_ID, S3_BUCKET_NAME, RAW_DATA_PREFIX, TRANSFORMED_DATA_PREFIX,
                              SNOWFLAKE_CONN_ID, CLEANSED_LAYER_SCHEMAS, SNOWFLAKE_STAGE, SNOWFLAKE_FILE_FORMAT)
# from include.validations.validations import validate_input
from include.etl.load_data_to_snowflake import load_dfs_to_sf


@dag(
    start_date=datetime(2026, 7, 1),
    schedule='@daily',
    catchup=False,
    tags=['etl'],
)
def etl_pipeline_dag():
    @task
    def extract_raw_data(bucket: str, folder: str, aws_conn_id: str):
        return extract_raw_data_paths_from_s3(bucket, folder, aws_conn_id)

    @task
    def transform_raw_data(file_paths: dict, aws_conn_id: str, bucket_name: str, transformation_prefix: str):
        return clean_data(file_paths, aws_conn_id, bucket_name, transformation_prefix)

    @task
    def merge_data(file_paths: dict, aws_conn_id: str, bucket_name: str, transformation_prefix: str):
        return merge_sales_and_product_data(file_paths, aws_conn_id, bucket_name, transformation_prefix)

    @task
    def load_to_snowflake(file_paths, snowflake_conn_id: str, schemas: dict, stage: str, file_format: str):
        return load_dfs_to_sf(file_paths, snowflake_conn_id, schemas, stage, file_format)


    raw_data_paths = extract_raw_data(S3_BUCKET_NAME, RAW_DATA_PREFIX, AWS_CONN_ID)
    transformed_data_paths = transform_raw_data(
        raw_data_paths,
        aws_conn_id=AWS_CONN_ID,
        bucket_name=S3_BUCKET_NAME,
        transformation_prefix=TRANSFORMED_DATA_PREFIX
    )


    validated_dfs_with_merged_path = merge_data(
        file_paths=transformed_data_paths,
        aws_conn_id=AWS_CONN_ID,
        bucket_name=S3_BUCKET_NAME,
        transformation_prefix=TRANSFORMED_DATA_PREFIX
    )

    load_to_snowflake(
        file_paths=validated_dfs_with_merged_path,
        snowflake_conn_id=SNOWFLAKE_CONN_ID,
        schemas=CLEANSED_LAYER_SCHEMAS,
        stage=SNOWFLAKE_STAGE,
        file_format=SNOWFLAKE_FILE_FORMAT
    )

etl_pipeline_dag()