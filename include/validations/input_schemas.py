import pandera as pa


GTE_ZERO_CHECK = pa.Check.ge(0, error='Value must be greater than or equal to zero')
GT_ZERO_CHECK = pa.Check.gt(0, error='Value must be greater zero')
ORDER_STATUS = ['Completed', 'Shipped', 'Pending', 'Returned']
ORDER_STATUS_LOWER = {status.lower() for status in ORDER_STATUS}


PRODUCTS_INPUT_SCHEMA = pa.DataFrameSchema({
    'product_id': pa.Column(int, nullable=False, unique=True),
    'category': pa.Column(str, nullable=False,),
    'brand': pa.Column(str, nullable=False,),
    'rating': pa.Column(float, nullable=False,),
    'in_stock': pa.Column(bool, nullable=False,),
    'launch_date': pa.Column('datetime64[us]', nullable=False,),
}, strict=True)


SALES_INPUT_SCHEMA = pa.DataFrameSchema({
    'sales_id': pa.Column(int, nullable=False, unique=True),
    'proDuct Id': pa.Column(int, nullable=False,),
    'Region': pa.Column(str, nullable=False,),
    'qty': pa.Column(int, nullable=False,checks=GT_ZERO_CHECK),
    'Price': pa.Column(float, nullable=False, checks=GTE_ZERO_CHECK),
    'Time stamp': pa.Column('datetime64[us]', nullable=False,),
    'discount': pa.Column(
        float,
        nullable=False,
        checks=pa.Check.in_range(0, 1, error='Value must be between 0 and 1'),
    ),
    'order_status': pa.Column(
        str,
        nullable=False,
        checks=pa.Check(
            lambda series: series.str.lower().isin(ORDER_STATUS_LOWER),
            error=f"Value has to be one of: {', '.join(ORDER_STATUS)}")
    ),
}, strict=True)