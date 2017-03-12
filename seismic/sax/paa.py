# -*- coding: utf-8 -*-
import numpy as np


class PaaError(Exception):
    pass


class Paa(object):
    def __init__(self, times, values):
        """
        Prepare a PAA (Piecewise Aggregate Approximation) object to calculate
        PAA of a given dataset

        Args:
            times (numpy.Array):  times in millisecods (can be epoch)
            values (numpy.Array): values
        """
        if not len(times) == len(values):
            raise PaaError("Lengths of times and values did not match")
        self.t = np.array(times)
        self.v = np.array(values)

    def paa(self, interval):
        """
        Calculate PAA.  Assumes time deltas are a factor of interval.  No
        regression. (this will bite me later.  TODO: np.linspace)

        Args:
            interval (int): Window size in ms

        Yields:
            (window start time in ms, value)
        """
        if not isinstance(interval, int):
            raise PaaError("interval should be an integer")
        v = self.v
        t = self.t

        start_pos = 0
        end_pos = 0

        while start_pos < len(t):
            t_start = t[start_pos]
            end_pos = np.searchsorted(t[start_pos:], t_start + interval) + start_pos
            if end_pos > len(t) - 1:
                raise StopIteration
            #t_end = t[end_pos]
            this_val = np.mean(v[start_pos:end_pos])
            this_time = t[start_pos]
            yield(this_time, this_val)
            start_pos = end_pos
        raise StopIteration