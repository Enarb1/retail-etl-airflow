from airflow.providers.amazon.aws.hooks.s3 import S3Hook


def get_s3_hook_and_storage_options(aws_conn_id: str) -> tuple[S3Hook, dict]:
    """
    Get S3 hook and storage options.
    """
    s3_hook = S3Hook(aws_conn_id=aws_conn_id)
    creds = s3_hook.get_credentials()

    storage_options = {
        'key': creds.access_key,
        'secret': creds.secret_key,
    }

    return s3_hook, storage_options
