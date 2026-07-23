import pandera as pa
import pandas as pd
from pandera.errors import SchemaErrors
from include.logger import set_up_logger
from include.validations.input_schemas import SALES_INPUT_SCHEMA, PRODUCTS_INPUT_SCHEMA
from include.validations.output_schemas import SALES_OUTPUT_SCHEMA, PRODUCTS_OUTPUT_SCHEMA, MERGED_SALES_PRODUCTS_OUTPUT_SCHEMA

logging = set_up_logger(__name__)


INPUT_SCHEMA_MAPPER = {
        'sales_data': SALES_INPUT_SCHEMA,
        'product_data': PRODUCTS_INPUT_SCHEMA,
    }


OUTPUT_SCHEMA_MAPPER = {
        'sales_data': SALES_OUTPUT_SCHEMA,
        'product_data': PRODUCTS_OUTPUT_SCHEMA,
        'merged_sales_product_data': MERGED_SALES_PRODUCTS_OUTPUT_SCHEMA,
    }


def validation_df(
        df: pd.DataFrame,
        file_name: str,
        schema_mapper: dict[str, pa.DataFrameSchema],
        rais_on_errors: bool = True
)-> pd.DataFrame | None:
    """
    Validate a DataFrame against the configured schema.

    When raise_on_error is False, validation failures are logged and the
    original DataFrame is returned so that processing can continue.
    """

    if file_name not in schema_mapper.keys():
        raise ValueError(f'File {file_name} has no input validation schema')

    schema = schema_mapper[file_name]
    logging.info(f'Validating {file_name}...')

    try:
        validated_df = schema.validate(df, lazy=True)
        logging.info(f'File {file_name} validated successfully')

        return validated_df

    except SchemaErrors as e:
        failure_cases = e.failure_cases
        logging.warning(f'File {file_name} contains {len(failure_cases)} validation issues')

        # Logging each row with an issue
        logging.warning(f'Validation problems for:\n'
                        f'{failure_cases.to_string(index=False)}')

        if rais_on_errors:
            raise

        logging.warning(f'Continue processing with original {file_name}')

        return df


def validate_output(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """
    Validating output data using the 'validation_df' function.
    Passing OUTPUT_SCHEMA_MAPPER and True on rais_on_errors.
    Returning the validated dataframe.
    """

    validated_df = validation_df(df, file_name, schema_mapper=OUTPUT_SCHEMA_MAPPER, rais_on_errors=True)

    return validated_df


def validate_input_data(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """
    Validating input data using the 'validation_df' function.
    Passing INPUT_SCHEMA_MAPPER and False on rais_on_errors.
    Returning the original dataframe.
    """
    input_df  = validation_df(df, file_name, schema_mapper=INPUT_SCHEMA_MAPPER, rais_on_errors=False)

    return input_df
