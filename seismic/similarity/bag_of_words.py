def bag_of_words(s, w):
    """
    Takes a string s and returns a sliding window array of substrings of
    length w

    Args:
        s: string
        w: length of word

    Returns:
        List
    """
    bow = [None] * (len(s) - w + 1)
    for i in range(0, len(s) - w + 1):
        bow[i] = s[i:i + w]
    return bow