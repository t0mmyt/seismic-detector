def is_true(s=str):
    """
    Checks if a string sounds truth-y (e.g. from a url encoded string)
    Args:
        s (string): string to check

    Returns:
        Boolean
    """
    return s.lower() in ["true", "yes", "y", "1"] if s else False