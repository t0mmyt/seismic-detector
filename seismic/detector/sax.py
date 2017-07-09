import types
from collections import deque

from .exceptions import DetectorError


def distance(alphabet, a, b):
    """
    Calculates the distance from the centre value in the alphabet of a given s

    Args:
        alphabet (str): alphabet to search
        a (str): First character
        b (str): Second character

    Returns:
        int: distance from centre value
    """
    if a not in alphabet:
        raise DetectorError("{} was not found in {}".format(a, alphabet))
    if b not in alphabet:
        raise DetectorError("{} was not found in {}".format(b, alphabet))
    return abs(alphabet.find(a) - alphabet.find(b))


def near_centre(alphabet, centre, max, s):
    """
    Returns whether a character is less than max from the centre value of a string

    Args:
        alphabet (str): full alphabet to compare from
        centre (str): centre value
        max (int): maximum distance to consider
        s (str): search character

    Returns:
        bool
    """
    return s == centre or distance(alphabet, centre, s) <= max


def sax_detect(stream, alphabet, paa_int, off_threshold=5000, min_len=5000):
    """

    Args:
        stream (types.GeneratorType): Generator of SAX string
        alphabet (str): Alphabet used to create SAX string
        paa_int (int): PAA Window size in ms
        off_threshold: Quiet period to consider event finished
        min_len: Minimum length of an event to yield

    Yields:
        (start_ms, end_ms)
    """
    if not isinstance(stream, types.GeneratorType):
        raise DetectorError(
            "SaxDetect stream expects a generator, got {}".format(type(stream)))
    if not isinstance(alphabet, str):
        raise DetectorError(
            "SaxDetect alphabet expects a str, got {}".format(type(alphabet)))
    if not len(alphabet) % 2 == 1:
        raise DetectorError(
            "SaxDetect requires an odd length of alphabet to have a centre")
    # Convert the next two values from ms to number of elements
    min_len = int(min_len / paa_int)
    off_threshold = int(off_threshold / paa_int)
    # Ring buffer for looking back at recent values
    buffer = deque([], maxlen=off_threshold)
    # Centre value to calculate distance from
    centre = alphabet[int(len(alphabet) / 2)]
    i = 0  # current pos
    t_on = 0  # trigger on value
    triggered = False
    for s in stream:
        buffer.appendleft(s)
        if not triggered:
            if not near_centre(alphabet, centre, 1, s):
                triggered = True
                t_on = i
        elif triggered:
            if near_centre(alphabet, centre, 1, s):
                for j in range(1, off_threshold):
                    if not near_centre(alphabet, centre, 1, buffer[j]):
                        break
                else:
                    triggered = False
                    if i - t_on >= min_len:
                        yield t_on * paa_int, (i - off_threshold) * paa_int
        i += 1

