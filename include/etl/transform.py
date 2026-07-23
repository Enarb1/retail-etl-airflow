import pandas as pd
from include.logger import set_up_logger
from include.s3_utils import get_s3_hook_and_storage_options
from include.etl.utils import read_data_from_s3
from include.validations.validations import validate_output, validate_input_data
from include.etl.load_s3_parquet import load_data_to_s3

logging = set_up_logger(__name__)


def headers_to_snake_case(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizing headers to snake case.
    """
    df = df.copy()
    logging.info(f"Converting headers {', '.join(map(str, df.columns))} to snake_case")

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(' ', '_')
    )

    logging.info(f"Converted all headers. Header names: {', '.join(df.columns)}")

    return df


def clean_products_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforming and cleaning the product data.
    Category column to string and standardizing category names.
    Brand colum to string and striping whitespaces.
    Launch date column to datetime.
    Returning the cleaned dataframe
    """
    df = df.copy()
    df['category'] = df['category'].astype('string').str.strip().str.title()
    df['brand'] = df['brand'].astype('string').str.strip()
    df['launch_date'] = pd.to_datetime(df['launch_date'], format='mixed', errors='coerce')
    return df


def clean_sales_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforming and cleaning the sales data.
    Filling missing region names with "Unknown" and standardizing region names.
    Removing rows with no price or price <= 0.
    Timestamp to datetime.
    Order Status to string and standardizing it.
    Returning the cleaned dataframe
    """
    df = df.copy()
    invalid_price_mask = (df['price'].isna() | df['price'].le(0))
    invalid_price_count = invalid_price_mask.sum()

    if invalid_price_count:
        logging.warning(f'Removing {invalid_price_count} rows.')

    df['region'] = df['region'].fillna('Unknown').astype('string').str.strip().str.title()
    df = df.loc[~invalid_price_mask].copy()
    df['time_stamp'] = pd.to_datetime(df['time_stamp'], format='mixed', errors='coerce')
    df['order_status'] = df['order_status'].astype('string').str.strip().str.title()
    df = df.rename(columns={
        'discount': 'discount_percentage',
    })
    df['discount_percentage'] = df['discount_percentage'].fillna(0)

    return df


def clean_data(
        file_paths: dict[str, str],
        aws_conn_id: str,
        bucket_name: str,
        transformation_prefix: str) -> dict[str, str]:
    """
    Cleaning the raw data using a mapping dictionary. Validating the input and transformed data.
    Loading the transformed data to the new S3 path and returning a dictionary with {'file_name': 's3_path'}
    """

    transformation_mapper = {
        'sales_data': clean_sales_df,
        'product_data': clean_products_df,
    }

    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)

    transformed_data = {}

    for file_name, s3_path in file_paths.items():
        if file_name not in transformation_mapper.keys():
            logging.warning(f'No transformation configured for {file_name}')
            continue

        df = read_data_from_s3(s3_path, storage_options)
        df = validate_input_data(df, file_name)
        df = headers_to_snake_case(df)
        logging.info(f'Cleaning column in  {file_name}')
        df = transformation_mapper[file_name](df)
        logging.info(f'Columns in {file_name} cleaned successfully!')

        validated_df = validate_output(df, file_name)

        transformed_path = f's3://{bucket_name}/{transformation_prefix}/{file_name}.parquet'
        load_data_to_s3(validated_df, transformed_path, storage_options)

        transformed_data[file_name] = transformed_path

    if not transformed_data:
        raise ValueError(f'No data was cleaned!')

    logging.info(f'Data cleaned successfully! Returning transformed data paths dictionary')

    return transformed_data


def merge_sales_and_product_data(
        file_paths: dict[str, str],
        aws_conn_id: str,
        bucket_name: str,
        transformation_prefix: str
) -> dict[str, str]:
    """
    Merging sales data and product data and loading the new dataframe to S3.
    Adding the new file path to the dictionary with file paths.
    Returning the updated dictionary with the merged data.
    """

    logging.info('Merging sales data and product data')
    _, storage_options = get_s3_hook_and_storage_options(aws_conn_id)

    dataframes_to_merge = {}

    logging.info('Getting dataframes...')

    for file_name, s3_path in file_paths.items():
        df = read_data_from_s3(s3_path, storage_options)
        dataframes_to_merge[file_name] = df

    sales_df = dataframes_to_merge['sales_data']
    product_df = dataframes_to_merge['product_data']

    try:
        merged_df = sales_df.merge(product_df, how='left', on='product_id', validate='many_to_one')
        logging.info('Merged sales data and product data successfully!')
    except Exception as e:
        logging.error(f'Error merging sales data and product data: {e}')
        raise

    logging.info('Adding discount amount column...')

    gross_revenue = merged_df['price'] * merged_df['qty']
    merged_df['discount_amount'] = gross_revenue * merged_df['discount_percentage']

    logging.info('Discount amount added successfully. Adding total revenue column...')

    merged_df['total_revenue'] = gross_revenue - merged_df['discount_amount']
    logging.info('Total revenue added successfully.')

    merged_df_filename = 'merged_sales_product_data'

    validated_merged_df = validate_output(merged_df, merged_df_filename)

    merged_df_path = f's3://{bucket_name}/{transformation_prefix}/{merged_df_filename}.parquet'
    load_data_to_s3(validated_merged_df, merged_df_path, storage_options)

    file_paths[merged_df_filename] = merged_df_path

    return file_paths