import unittest
import numpy as np

from ..utils import bag_of_words, remove_outlier


class BagOfWordsTest(unittest.TestCase):
    def setUp(self):
        self.sample = "abdcefghijkl"

    def test_w_1(self):
        bow = bag_of_words(self.sample, 1)
        self.assertEqual(bow[-1], "l")
        self.assertEqual(len(bow), 12)

    def test_w_3(self):
        bow = bag_of_words(self.sample, 3)
        self.assertEqual(bow[-1], "jkl")
        self.assertEqual(len(bow), 10)

    def test_w_5(self):
        bow = bag_of_words(self.sample, 5)
        self.assertEqual(bow[-1], "hijkl")
        self.assertEqual(len(bow), 8)


class RemoveOutlierTest(unittest.TestCase):
    def test_1(self):
        a = np.array([1, 2, 3, 5, 3])
        self.assertTrue(np.array_equal(remove_outlier(a), np.array([1, 2, 3, 3])))
