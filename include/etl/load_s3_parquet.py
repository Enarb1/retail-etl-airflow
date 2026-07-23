import pandas as pd
from include.logger import set_up_logger

logging = set_up_logger(__name__)

def load_data_to_s3(df: pd.DataFrame, s3_path: str, storage_options: dict) -> None:
    """
    Loads data to a S3 path as parquet
    """
    logging.info(f'Writing data to {s3_path}...')
    try:
        df.to_parquet(s3_path, storage_options=storage_options, index=False)
        logging.info(f'Successfully wrote data to {s3_path}')
    except Exception as e:
        logging.exception(f'Cannot write to {s3_path}. Error: {e}')
        raise
