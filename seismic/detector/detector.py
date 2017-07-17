from abc import ABC, abstractmethod
import numpy as np
from obspy.signal.filter import bandpass

from .exceptions import DetectorError


class Detector(ABC):
    """
    Base class for a detector
    """
    @abstractmethod
    def __init__(self, trace, sampling_rate):
        if not isinstance(trace, np.ndarray):
            raise DetectorError("Trace should be an ndarray")
        self.trace = trace
        self.freq = sampling_rate
        self.interval = 1000 / sampling_rate
        self._abs = None

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

    def bandpass(self, low, high):
        """
        Perform a frequency bandpass in-place on a trace to reduce noise

        Args:
            low:  Remove frequencies below this value
            high: Remove frequencies above this value
        """
        self.trace = bandpass(self.trace, low, high, self.freq)

    @abstractmethod
    def detect(self, *args, **kwargs):
        pass
