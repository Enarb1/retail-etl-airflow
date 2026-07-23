import pandera as pa

from include.validations.input_schemas import GTE_ZERO_CHECK, GT_ZERO_CHECK


VALID_REGIONS = ['Unknown', 'East', 'West', 'North', 'South']
ORDER_STATUS = ['Completed', 'Shipped', 'Pending', 'Returned']
IS_TITLE_CHECK = pa.Check(lambda s: s.str.istitle(), error='String value must be title')

PRODUCTS_OUTPUT_SCHEMA = pa.DataFrameSchema({
    'product_id': pa.Column('int64', nullable=False, unique=True),
    'category': pa.Column('string', nullable=False, checks=IS_TITLE_CHECK),
    'brand': pa.Column('string', nullable=False),
    'rating': pa.Column(
        float,
        nullable=False,
        checks=pa.Check.in_range(0, 5, error='Rating must be between 0 and 5')
    ),
    'in_stock': pa.Column(bool, nullable=False),
    'launch_date': pa.Column('datetime', nullable=True),
}, strict=True)


SALES_OUTPUT_SCHEMA = pa.DataFrameSchema({
    'sales_id': pa.Column('int64', nullable=False, unique=True),
    'product_id': pa.Column('int64', nullable=False),
    'region': pa.Column('string', nullable=False, checks=pa.Check.isin(
        VALID_REGIONS,
        error=f"Region must be one of: {', '.join(VALID_REGIONS)}"
    )),
    'qty': pa.Column('int64', checks=GT_ZERO_CHECK , nullable=False),
    'price': pa.Column(float, checks=GTE_ZERO_CHECK ,nullable=False),
    'time_stamp': pa.Column('datetime', nullable=False),
    'discount_percentage': pa.Column(
        float,
        nullable=False,
        checks=pa.Check.in_range(0, 1, error='Value must be between 0 and 1'),
    ),
    'order_status': pa.Column('string', nullable=False, checks=pa.Check.isin(
        ORDER_STATUS,
        error=f"Order status must be one of: {', '.join(ORDER_STATUS)}"
    )),
}, strict=True)


MERGED_SALES_PRODUCTS_OUTPUT_SCHEMA = pa.DataFrameSchema({
    'sales_id': pa.Column('int64', nullable=False, unique=True),
    'product_id': pa.Column('int64', nullable=False),
    'region': pa.Column('string', nullable=False, checks=pa.Check.isin(
        VALID_REGIONS,
        error=f"Region must be one of: {', '.join(VALID_REGIONS)}"
    )),
    'qty': pa.Column('int64', checks=GT_ZERO_CHECK , nullable=False),
    'price': pa.Column(float, checks=GTE_ZERO_CHECK ,nullable=False),
    'time_stamp': pa.Column('datetime', nullable=False),
    'discount_percentage': pa.Column(
        float,
        nullable=False,
        checks=pa.Check.in_range(0, 1, error='Value must be between 0 and 1'),
    ),
    'order_status': pa.Column('string', nullable=False, checks=pa.Check.isin(
        ORDER_STATUS,
        error=f"Order status must be one of: {', '.join(ORDER_STATUS)}"
    )),
    'category': pa.Column('string', nullable=False, checks=IS_TITLE_CHECK),
    'brand': pa.Column('string', nullable=False),
    'rating': pa.Column(
        float,
        nullable=False,
        checks=pa.Check.in_range(0, 5, error='Rating must be between 0 and 5')
    ),
    'in_stock': pa.Column(bool, nullable=False),
    'launch_date': pa.Column('datetime', nullable=True),
    'discount_amount' : pa.Column(float, nullable=False, checks=GTE_ZERO_CHECK),
    'total_revenue' : pa.Column(float, nullable=False, checks=GTE_ZERO_CHECK),
}, strict=True)