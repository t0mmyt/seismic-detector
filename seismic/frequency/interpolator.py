def is_positive(n=float):
    """
    Checks if n is positive (incl zero)

    Args:
        n (float): Number to check

    Returns:
        bool
    """
    return n >= 0


def zero_intersect(d0=float, d1=float, interval=float):
    """
    Uses the ratio of the change between d0 and d1 against the "interval" to
    interpolate where the zero intersection was

    Args:
        d0 (float): First datapoint
        d1 (float): Second datapoint
        interval (float): time delta between datapoints

    Returns:
        linearly interpolated x-axis intersect
    """
    y1 = abs(d1 - d0)
    y2 = y1 - abs(d1)
    return (interval * y2) / y1


def phase_inversions(data, interval):
    """
    Scans through data looking for phase inversions (i.e -ve to +ve or +ve to -ve)

    Args:
        data (list:float): data to search
        interval (float): time delta between datapoints

    Yields:
        float of offsets from zero (e.g. milliseconds)
    """
    for i in range(1, len(data)):
        if is_positive(data[i - 1]) != is_positive(data[i]):
            # Phase change happened
            yield (i - 1) * interval + zero_intersect(data[i - 1], data[i], interval)


def frequency(data, interval):
    """
    Use the phase_inversion with interpolated zero intersections to return frequency
    as a function of time

    Args:
        data (list:float): data to run against
        interval (float): time delta between endpoints in ms

    Returns:

    """
    last_d = None
    for d in phase_inversions(data, interval):
        if last_d is None:
            last_d = d
            continue
        yield ((d - last_d) / 2 + d), 500 / (d - last_d)  # 500 because we a looking for half cycles over milliseconds
        last_d = d
