import pandas as pd

from pathlib import PurePosixPath
from include.logger import set_up_logger

logging = set_up_logger(__name__)

def read_parquet_df(s3_path: str, storage_options: dict) -> pd.DataFrame:
    """
    Read a parquet file from s3.
    """
    df = pd.read_parquet(s3_path, storage_options=storage_options)
    return df


def read_json_df(s3_path: str, storage_options: dict) -> pd.DataFrame:
    """
    Read a JSON file from s3.
    """
    df = pd.read_json(s3_path, storage_options=storage_options,)
    return df


def read_csv_df(s3_path: str, storage_options: dict) -> pd.DataFrame:
    """
    Read a csv file from s3.
    """
    df = pd.read_csv(s3_path, storage_options=storage_options)
    return df


def read_data_from_s3(s3_path: str, storage_options: dict) -> pd.DataFrame:
    """
    Reads data from a S3 path. Supports csv, json, parquet. Returns a Dataframe.
    """
    read_mapper = {
        '.csv': read_csv_df,
        '.json': read_json_df,
        '.parquet': read_parquet_df,
    }

    file_type = PurePosixPath(s3_path).suffix.lower()

    if file_type not in read_mapper.keys():
        raise ValueError(f'File type {file_type} is not supported')

    logging.info(f'Reading data from {s3_path}')

    try:
        df = read_mapper[file_type](s3_path, storage_options)
    except Exception as e:
        logging.error(f'Cannot read file from {s3_path}. Error: {e}')
        raise

    logging.info(f'Successfully read file from {s3_path}\nRead file with {len(df)} rows and {len(df.columns)} columns')

    return df