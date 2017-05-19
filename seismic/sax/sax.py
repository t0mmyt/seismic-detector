from scipy.stats import norm
import numpy as np
from pandas import Series


class SaxError(Exception):
    pass


class Sax(object):
    def __init__(self, paa=Series):
        """
        Provides a generator for SAX data from PAA
        Args:
            paa: 
        """
        if not isinstance(paa, Series):
            raise SaxError("paa should be a pandas.Series, got {}".format(type(paa)))
        self.paa = paa

    def __call__(self, alphabet=str):
        """
        Generate SAX string from PAA as a pandas.Series
        
        Args:
            alphabet (str): alphabet for SAX

        yields:
            str
        """
        if not isinstance(alphabet, str):
            raise SaxError("alphabet should be a str, got {}".format(type(alphabet)))
        # Generate gaussian breakpoints
        thresholds = norm.ppf(
            np.linspace(1 / len(alphabet), 1 - 1 / len(alphabet), len(alphabet) - 1)
        )
        for i in self.paa:
            yield alphabet[np.searchsorted(thresholds, i)]