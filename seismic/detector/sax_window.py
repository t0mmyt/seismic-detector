import types
from collections import deque
import pandas as pd

from seismic.sax import Paa, PaaError, Sax, SaxError
from .detector import Detector
from .exceptions import DetectorError


class SaxDetectWindow(Detector):
    def __init__(self, trace, samping_rate):
        super().__init__()

    def detect(self, alphabet, paa_int, off_threshold, min_lin, window_size):
        pass
