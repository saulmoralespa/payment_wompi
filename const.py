
SUPPORTED_CURRENCIES = [
    'COP'
]


# Mapping of transaction states to Wompi payment statuses.
PAYMENT_STATUS_MAPPING = {
    'pending': ['pending'],
    'done': ['successful'],
    'cancel': ['cancelled'],
    'error': ['failed'],
}