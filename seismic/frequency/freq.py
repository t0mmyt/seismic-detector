# -*- coding: utf-8 -*-
import numpy as np
#import pandas as pd

class FrequencyError(Exception):
    pass


class Frequency(object):
    def __init__(self, data, sampling_rate):
        """
        An object for esimating the frequency modulation of a dataset.
        
        Args:
            data (ndarray): Numerical numpy array of datapoints
            sampling_rate (float): Sample rate in Hz of datapoints
        """        
        assert isinstance(data, np.ndarray), "data should be a numpy array"
        self.data = data
        self.sampling_rate = sampling_rate
        self.interval = 1000 / sampling_rate
        
    def find_inversions(self):
        """
        Find phase inversions on the data.  Yield the value to the right of the inversion 
        
        Yields:
            Index of sample on the RHS of a phase inversion
        """
        phase_positive = True if self.data[0] >= 0 else False
        i = 0
        while i < len(self.data):
            print(phase_positive)
            dd = self.data[i:]
            if phase_positive:
                i = np.argmin(dd<0) + 1  # Find the next occurance below 0
                phase_positive = False
                yield i
            else:
                i = np.argmax(dd>0) + 1
                phase_positive = True  # Find the next occurance above 0
                yield i
            i = len(self.data)
                
    def zero_by_regression(self):
        """
        Return values in ms from start of sample where phase changes using the tangent between
        the two points to estimate the actual point of inversion.
        
        Yields:
            ms from start of sample
        """
        for i in self.find_inversions():
            if self.data[i] == 0:
                yield i
            else:
                y1 = abs(self.data[i - 1])  # Distance of first point from zero
                y2 = abs(self.data[i])  # Distance of second point from zero
                l = (y2 * (y1 + y2)/self.interval)  # Find zero crossing point with some trig
                # If our RHS value is +ve then we are going from -ve > +ve, else the other way around
                if self.data[i] > 0:
                    yield i * self.interval - l  # We want the RHS distance
                if self.data[i] < 0:
                    yield (i - 1) * self.interval + l  # We want the LHS distance
                
    def left_frequency(self):
        """
        Uses the distance from the previous value to estimate a point in time frequency
        
        Yields:
            Float: Offset from start in ms
            Float: Frequency in Hz
        """
        last_i = None
        for i in self.zero_by_regression():
            if not last_i:
                last_i = i
                continue
            yield i, (i - last_i) / 2000
                
                
            