
TYPE_DICT = {
    'str': str,
    'float': float,
    'int': int,
    'bool': bool
}

def str_to_type(str_type):
    """Convert a string to a type

    Args:
        str_type (str): A string representing a type such as 'str' or 'bool'

    Raises:
        ValueError: When a string with no corresponding type definition is supplied

    Returns:
        Any: The type being converted to
    """
    fetch_type = TYPE_DICT.get(str_type.lower())
    if fetch_type is None:
        raise ValueError('Invalid or unsupported type: {}'.format(str_type.lower()))
    return fetch_type
