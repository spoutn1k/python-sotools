def flatten(nested_list):
    """Flatten a nested list."""
    return [item for sublist in nested_list for item in sublist]
