def jaccard(a, b):
    """
    Calculate the Jaccard Similarity Coefficient of two input sets

    Args:
        a: First set
        b: Second Set

    Returns:
        Float
    """
    a = set(a)
    b = set(b)
    union = float(len(a.union(b)))
    intersection = float(len(a.intersection(b)))
    return intersection / union if (union + intersection) > 0 else 1
