import unittest

from ..jaccard import jaccard


class JaccardTest(unittest.TestCase):
    def test_len_zero(self):
        a = []
        b = []
        self.assertEqual(jaccard(a, b), 1)

    def test_similar(self):
        a = [1, 2, 3]
        b = [3, 2, 1]
        self.assertEqual(jaccard(a, b), 1)

    def test_dissimilar(self):
        a = [1, 2, 3]
        b = [4, 5, 6]
        self.assertEqual(jaccard(a, b), 0)

    def test_score(self):
        a = [0, 1, 2, 5, 6]
        b = [0, 2, 3, 5, 7, 9]
        self.assertEqual(jaccard(a, b), 0.375)

    def test_score_reversed(self):
        a = [0, 2, 3, 5, 7, 9]
        b = [0, 1, 2, 5, 6]
        self.assertEqual(jaccard(a, b), 0.375)

    def test_strings_with_repetition(self):
        a = "abcfggg"
        b = "aacdfhj"
        self.assertEqual(jaccard(a, b), 0.375)
