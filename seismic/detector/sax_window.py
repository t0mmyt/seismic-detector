import types
from collections import deque
import pandas as pd
import numpy as np

from seismic.sax import Paa, PaaError, Sax, SaxError
from .detector import Detector
from .sax import SaxDetect
from .exceptions import DetectorError


class SaxDetectWindow(Detector):
    def __init__(self, trace, sampling_rate):
        super().__init__(trace, sampling_rate)
        # Some nasty data munging to get around weird sampling rates
        end_time = len(trace) * (1000 / sampling_rate)
        timestamps = np.linspace(0, end_time, num=len(trace))
        rng = pd.to_datetime(timestamps, unit="ms")
        self.series = pd.Series(data=trace, index=rng)

    def detect(self, alphabet, paa_int, off_threshold, min_lin, window_size):
        pass
