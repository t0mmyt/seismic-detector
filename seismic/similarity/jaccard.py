def jaccard(a, b):
    a = set(a)
    b = set(b)
    union = float(len(a.union(b)))
    intersection = float(len(a.intersection(b)))
    return intersection / union if (union + intersection) > 0 else 1
