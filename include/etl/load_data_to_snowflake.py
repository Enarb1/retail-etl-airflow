from include.logger import set_up_logger
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook



logging = set_up_logger(__name__)


def load_dfs_to_sf(file_paths: dict, snowflake_conn_id: str,  schemas: dict, stage: str, file_format: str) -> None:
    """
    ELT load step. The transformed and validated files already sit in S3 as Parquet and are visible through the
    Snowflake stage. For each file it issues a TRUNCATE and COPY INTO so Snowflake reads the file directly from
    S3 and loads it into the target table
    """
    logging.info('Starting Snowflake load vie COPY INTO...')

    sf_hook = SnowflakeHook(snowflake_conn_id=snowflake_conn_id)

    for file_name, s3_path in file_paths.items():
        if file_name not in schemas:
            logging.warning(f'No Snowflake target configuration for {file_name}. Skipping.')
            continue

        database, schema, table = schemas[file_name]
        object_name = s3_path.rsplit('/', 1)[-1]
        target = f'{database}.{schema}.{table}'
        stage_path = f'@{database}.{schema}.{stage}/{object_name}'

        truncate_sql = f'TRUNCATE TABLE IF EXISTS {target};'

        copy_sql = f"""
            COPY INTO {target}
            FROM {stage_path}
            FILE_FORMAT = (FORMAT_NAME = {database}.{schema}.{file_format})
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
            ON_ERROR = 'ABORT_STATEMENT'
            FORCE = TRUE
            PURGE = FALSE
        """

        logging.info(f'Loading {file_name} into {target} via COPY INTO from {stage_path}...')

        try:
            sf_hook.run(truncate_sql)
            result = sf_hook.run(copy_sql, handler=lambda cur: cur.fetchone())
            logging.info(f'COPY INTO result for {target}: {result}')
            logging.info(f'Successfully loaded {file_name} into {target}!')
        except Exception as e:
            logging.error(f'Failed to load {file_name} into {target} from {stage_path}. Error: {e}')
            raise


    logging.info('Successfully loaded all files to Snowflake')
