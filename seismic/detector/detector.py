# -*- coding: utf-8 -*-
from logging import debug
import numpy as np
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
        
    @property
    def abs(self):
        """
        Absolute values of trace
        """
        if not hasattr(self, "_abs"):
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
#            long_window = Detector.normalised_to_peak(self.abs[i - long_window_length:i])
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
        long_window_length = int(long / self.interval)
        short_window_length = int(short / self.interval)
        iter_len = int(short_window_length / 2)
        trigger_len = int(trigger_len / self.interval)
        debug("Window lengths: {}, {} ({}s, {}s)".format(
            long_window_length, short_window_length, long/1000, short/1000))
        i = long_window_length + short_window_length
        triggered = False
        while i + short_window_length < len(self.trace):
            long_window = self.abs[i - long_window_length - short_window_length:i - short_window_length]
            long_window_mean = np.mean(long_window)
            long_window_std = np.std(long_window)
            short_window_mean = np.mean(self.abs[i - short_window_length:i])
            if not triggered:
                if short_window_mean > (long_window_mean + (long_window_std * nstds)):
                    off_threshold = long_window_mean# + (long_window_std * nstds)
#                    print(off_threshold)
                    triggered = True
                    triggered_obs = 1
#                    print(i)
            else: # if triggered
                triggered_obs += iter_len
                if short_window_mean < off_threshold: # trigger over
#                    print(off_threshold)
                    triggered = False
                    if triggered_obs > trigger_len:
                        yield(int(i - triggered_obs - (short_window_length / 2)), i)
                    triggered_obs = 0
            i += iter_len
            
#    def multiwindow(self, before_len, after_len, delay_offset, delay_len, alpha):
#         before_len = int(before_len / self.interval)
#         after_len = int(after_len / self.interval)
#         delay_len = int(delay_len / self.interval)
#         delay_offset = int(delay_offset / self.interval)
#         
#         i = before_len + delay_len + delay_offset
#         while i <= len(self.abs - after_len):
#             dta = np.mean(self.abs[i - delay_offset - delay_len:i - delay_len])
#             H1 = dta + (alpha * np.std(self.abs[i - delay_offset - delay_len:i - delay_len]))
#             R1 = self.abs[i]
#             if R1 > H1:
#                 bta = np.mean(self.abs[i - before_len:i])
#                 ata = np.mean(self.abs[i:i + after_len])
#                 R2 = ata / bta
#                 R3 = dta / bta
#                 
#             i += 100