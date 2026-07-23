import yaml
from pathlib import Path



CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_config():
    """Load the project configuration"""
    with open(CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError(f'Invalid or empty configuration file: {CONFIG_PATH}')

    return config

CONFIG = load_config()

AWS_CONN_ID = CONFIG['aws']['conn_id']
S3_BUCKET_NAME = CONFIG['aws']['bucket_name']

RAW_DATA_PREFIX = CONFIG['aws']['folders']['raw_data'].strip("/")
TRANSFORMED_DATA_PREFIX = CONFIG['aws']['folders']['transformed_data'].strip("/")


SNOWFLAKE_CONN_ID = CONFIG['snowflake']['conn_id']
SNOWFLAKE_DB = CONFIG['snowflake']['database']
SNOWFLAKE_STAGE = CONFIG['snowflake']['stage']
SNOWFLAKE_FILE_FORMAT = CONFIG['snowflake']['file_format']

SALES_CLEAN_SCHEMA = CONFIG['snowflake']['targets']['sales']['schema']
PRODUCT_CLEAN_SCHEMA = CONFIG['snowflake']['targets']['products']['schema']
SALES_SUMMARY_SCHEMA  = CONFIG['snowflake']['targets']['sales_summary']['schema']

SALES_CLEAN_TABLE = CONFIG['snowflake']['targets']['sales']['table']
PRODUCT_CLEAN_TABLE = CONFIG['snowflake']['targets']['products']['table']
SALES_SUMMARY_TABLE  = CONFIG['snowflake']['targets']['sales_summary']['table']


CLEANSED_LAYER_SCHEMAS = {
    'merged_sales_product_data': (SNOWFLAKE_DB, SALES_SUMMARY_SCHEMA, SALES_SUMMARY_TABLE),
    'sales_data': (SNOWFLAKE_DB, SALES_CLEAN_SCHEMA, SALES_CLEAN_TABLE),
    'product_data': (SNOWFLAKE_DB, PRODUCT_CLEAN_SCHEMA, PRODUCT_CLEAN_TABLE),
}