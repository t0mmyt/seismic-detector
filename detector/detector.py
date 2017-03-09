# -*- coding: utf-8 -*-
from logging import debug
import numpy as np
from obspy.signal.filter import bandpass


class DetectorError(Exception):
    pass


class Detector(object):
    def __init__(self, stream, sampling_rate):
        self.stream = stream
        self.freq = sampling_rate
        self.interval = 1000 / sampling_rate
        
    @property
    def abs(self):
        """
        Absolute values of stream
        """
        if not hasattr(self, "_abs"):
            self._abs = np.abs(self.stream)
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
        Perform a frequency bandpass in-place on a stream to reduce noise
        
        Args:
            low:  Remove frequencies below this value
            high: Remove frequencies above this value
        """
        self.stream = bandpass(self.stream, low, high, self.freq)

    def detect(self, short, long, nstds=1):
        """
        Run a hackish STA-LTA like detection on stream.  Normalises long window to 1 and looks for short window means
        above nstds standard deviations from the long window mean.
        
        Args:
            short: int: number of milliseconds for short window
            long:  int: number of milliseconds for long window
            nstds: float: number of standard deviations from long window mean to trigger on
            
        Yields:
            (time from start, long window mean, short window mean)        
        """
        long_window_length = int(long * self.interval)
        short_window_length = int(short * self.interval)
        debug("Window lengths: {}, {} ({}s, {}s)".format(
            long_window_length, short_window_length, long/1000, short/1000))
        i = long_window_length
        while i + short_window_length < len(self.stream):
            long_window = Detector.normalised_to_peak(self.abs[i - long_window_length:i])
            long_window_mean = np.mean(long_window)
            long_window_std = np.std(long_window)
            short_window_mean = np.mean(long_window[-short_window_length:])
            if short_window_mean > (long_window_mean + (long_window_std * nstds)):
                yield(i, long_window_mean, short_window_mean)
            i += short_window_length