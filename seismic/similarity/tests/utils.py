import unittest
import numpy as np

from .. import remove_outlier


class RemoveOutlierTest(unittest.TestCase):
    def test_1(self):
        a = np.array([1, 2, 3, 5, 3])
        self.assertTrue(np.array_equal(remove_outlier(a), np.array([1, 2, 3, 3])))
