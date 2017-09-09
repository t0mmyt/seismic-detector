from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from obspy.signal.filter import bandpass

from .exceptions import DetectorError


class Detector(ABC):
    """
    Base class for a stalta_detector
    """
    def __init__(self, trace, sampling_rate):
        if not isinstance(trace, np.ndarray):
            raise DetectorError("Trace should be an ndarray")
        self.trace = trace
        self.freq = sampling_rate
        self.interval = 1000 / sampling_rate
        self._abs = None
        # Some nasty data munging to get around weird sampling rates
        end_time = len(trace) * (1000 / sampling_rate)
        timestamps = np.linspace(0, end_time, num=len(trace))
        rng = pd.to_datetime(timestamps, unit="ms")
        self.series = pd.Series(data=trace, index=rng)

    @abstractmethod
    def detect(self, *args, **kwargs):
        pass

    @property
    def abs(self):
        """
        Absolute values of trace
        """
        if self._abs is None:
            self._abs = np.abs(self.trace)
        return self._abs

    @staticmethod
    def normalised_to_peak(a):
        """
        Divide all values in a by the maximum value

        Args:
            a:

        Returns:
            np.ndarray
        """
        assert isinstance(a, np.ndarray), "normalisation only works on numpy arrays"
        d = np.divide(a, max(np.max(a), -np.min(a)))
        return d

    def znormalise(self):
        std = np.std(self.series)
        mean = np.mean(self.series)
        self.series = (self.series - mean) / std

    def bandpass(self, low, high):
        """
        Perform a frequency bandpass in-place on a trace to reduce noise

        Args:
            low:  Remove frequencies below this value
            high: Remove frequencies above this value
        """
        self.trace = bandpass(self.trace, low, high, self.freq)

    def slice(self, start, end):
        ind_start = self.series.index.searchsorted(pd.to_datetime(start, unit="ms"))
        ind_end = self.series.index.searchsorted(pd.to_datetime(end, unit="ms"))
        return self.series[ind_start:ind_end]

