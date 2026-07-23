import pandas as pd

from pathlib import PurePosixPath
from  include.logger import  set_up_logger
from include.s3_utils import get_s3_hook_and_storage_options

logging = set_up_logger(__name__)

def extract_raw_data_paths_from_s3(bucket: str, folder: str, aws_conn_id: str) -> dict[str, str]:
    """
    Extract raw data paths from S3 bucket. Returning a dictionary {'dataset_name': 's3_path'}
    """
    logging.info(f'Extracting raw data paths from S3 bucket {bucket}/{folder}')

    s3_hook , storage_options = get_s3_hook_and_storage_options(aws_conn_id=aws_conn_id)
    keys = s3_hook.list_keys(bucket_name=bucket, prefix=folder)

    supported_filetypes = ['.csv', '.json', '.parquet']

    logging.info(f'Found {len(keys)} dataset paths')

    if not keys:
        raise  FileNotFoundError(f'No keys found in {bucket}/{folder}')

    raw_data_paths = {}

    for key in keys:
        # key ex.: regular-exam/raw-data/sales_data.csv

        # Key to PurePosixPath in order do get the file extension and dataset name
        path = PurePosixPath(key)
        extension = path.suffix.lower()

        if extension not in supported_filetypes:
            logging.info(f'Skipping {key} as it is not a supported file type')
            continue

        logging.info(f'Found valid key: {key}')

        s3_path = f's3://{bucket}/{key.lstrip("/")}'
        dataset_name = path.stem.lower()

        if dataset_name in raw_data_paths.keys():
            raise ValueError(f'Duplicate dataset name: {dataset_name}')

        logging.info(f'Adding {dataset_name}  with path: {s3_path}')
       #  key - value ex.: {'sales_data': s3://datawarehouse-etl-softuni/regular-exam/raw-data/sales_data.csv}
        raw_data_paths[dataset_name] = s3_path

    if not raw_data_paths:
        raise FileNotFoundError(f'No dataset paths found in {bucket}/{folder}')

    logging.info(f'Found {len(raw_data_paths)} dataset paths')

    return raw_data_paths
