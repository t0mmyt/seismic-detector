# -*- coding: utf-8 -*-
from logging import debug, info
import numpy as np
import pandas as pd
from obspy.signal.filter import bandpass


class DetectorError(Exception):
    pass


class Detector(object):
    def __init__(self, trace, sampling_rate):
        """
        Create a new Detector object

        Args:
            trace (np.ndarray): raw trace
            sampling_rate (int): Sample rate of trace in Hz
        """
        assert isinstance(trace, np.ndarray), "Trace should be an ndarray"
        self.trace = trace
        self.freq = sampling_rate
        self.interval = 1000 / sampling_rate
        self._abs = None
        self.trigger_values = None

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
        
    def windows(self, short, long, nstds=1):
        long_window_length = int(long / self.interval)
        short_window_length = int(short / self.interval)
        debug("Window lengths: {}, {} ({}s, {}s)".format(
            long_window_length, short_window_length, long/1000, short/1000))
        i = long_window_length
        while i + short_window_length < len(self.trace):
            # long_window = Detector.normalised_to_peak(self.abs[i - long_window_length:i])
            long_window = self.abs[i - long_window_length:i]
            long_window_mean = np.mean(long_window)
            long_window_std = np.std(long_window)
            short_window_mean = np.mean(long_window[-short_window_length:])
            yield(i, long_window_mean, nstds * long_window_std, short_window_mean)
            i += short_window_length

    def detect(self, short, long, nstds=1, trigger_len=500):
        """
        Run a hackish STA-LTA like detection on trace. Looks for short window means
        above nstds standard deviations from the long window mean for more than trigger_len observations.
        
        Args:
            short: int: number of ms for short window
            long: int: number of ms for long window
            nstds: float: number of standard deviations from long window mean to trigger on
            trigger_len: int: length in ms of short mean observations being above nstds to trigger on
            
        Yields:
            (time from start, long window mean, short window mean)        
        """
        trigger_values = []

        long_window_length = int(long / self.interval)
        short_window_length = int(short / self.interval)
        # iter_len = int(short_window_length / 2)
        iter_len = 1
        trigger_len = int(trigger_len / self.interval)  # Convert from ms to number of obs
        debug("Window lengths: {}, {} ({}s, {}s)".format(
            long_window_length, short_window_length, long/1000, short/1000))
        i = long_window_length + short_window_length
        triggered = False
        off_threshold = 0
        triggered_obs = 0
        while i + short_window_length < len(self.trace):
            long_window = self.abs[i - long_window_length - short_window_length:i - short_window_length]
            long_window_mean = np.mean(long_window)
            long_window_std = np.std(long_window)
            short_window_mean = np.mean(self.abs[i - short_window_length:i])
            trigger_values.append((i * self.interval, short_window_mean, long_window_mean, long_window_std * nstds))
            if not triggered:
                if short_window_mean > (long_window_mean + (long_window_std * nstds)):
                    off_threshold = long_window_mean
                    triggered = True
                    triggered_obs = 1
            else:  # if triggered
                triggered_obs += iter_len
                if short_window_mean < off_threshold:  # trigger over
                    triggered = False
                    if triggered_obs > trigger_len:
                        yield(
                            int(i - triggered_obs - (short_window_length / 2)) * self.interval,
                            i * self.interval
                        )
                    triggered_obs = 0
            i += iter_len
        # Get trigger values
        self.trigger_values = pd.DataFrame(
            trigger_values,
            columns=("t", "sm", "lm", "trigger"),
        )
