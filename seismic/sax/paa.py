import numpy as np
import pandas as pd


class PaaError(Exception):
    pass


class Paa(object):
    def __init__(self, series=pd.Series, normalise=True):
        """
        Prepare a PAA (Piecewise Aggregate Approximation) object to calculate
        PAA of a given dataset.  Will perform z-normalisation by default on
        data     before interpolating linearly to an interval of 1ms.

        Args:
            series (DataFrame): pandas DataFrame with time as index
            normalise (bool): Whether or not to normalise
        """
        if not isinstance(series, pd.Series):
            raise PaaError("series should be a pandas Series")
        series = series.resample("1L").mean().interpolate(method="time")
        if normalise:
            std = np.std(series)
            mean = np.mean(series)
            series = (series - mean) / std
        self.series = series

    def __call__(self, window=int):
        """
        Return a PAA of the DataFrame
        
        Args:
            window (int): Number of milliseconds in window 

        Returns:
            pandas.Series
        """
        if not isinstance(window, int):
            raise PaaError("Window should be an integer")
        df = self.series.copy()
        return df.resample("{}L".format(window)).mean().interpolate(method="time")
