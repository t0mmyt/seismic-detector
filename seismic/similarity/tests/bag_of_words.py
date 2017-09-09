import unittest
from .. import bag_of_words


class BagOfWordsTest(unittest.TestCase):
    def setUp(self):
        self.sample = "abdcefghijkl"

    def test_w_1(self):
        bow = bag_of_words(self.sample, 1)
        self.assertEqual(bow[-1], "l")
        self.assertEqual(len(bow), len(self.sample))

    def test_w_3(self):
        bow = bag_of_words(self.sample, 3)
        self.assertEqual(bow[-1], "jkl")
        self.assertEqual(len(bow), 10)

    def test_w_5(self):
        bow = bag_of_words(self.sample, 5)
        self.assertEqual(bow[-1], "hijkl")
        self.assertEqual(len(bow), 8)