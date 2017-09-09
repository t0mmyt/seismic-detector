import unittest
import pandas as pd
from iso8601 import parse_date

from seismic.sax import Paa, Sax


class PaaTest(unittest.TestCase):
    def setUp(self):
        self.start = parse_date("1970-01-01 00:00:00Z")
        self.end = parse_date("1970-01-01 00:00:04Z")
        self.duration = (self.end - self.start).seconds
        print(self.duration)
        self.data = [-2, -1, -.5, 0, .5]
        self.rng = pd.date_range(
            start=self.start,
            end=self.end,
            freq="1s"
        )
        self.series = pd.Series(data=self.data, index=self.rng)

    def test_paa(self):
        s = self.series
        self.assertEquals(len(s), len(self.data), "Series was wrong length")
        p = Paa(s)
        expected_paa_len = self.duration * 1000 + 1
        self.assertEqual(len(p.series), expected_paa_len, "Paa was wrong length")
        res = p(500)
        # self.assertAlmostEqual(res[1], -1.250, 3, "PAA calculation was off")
        # TODO assert time offset is + 0.5 * interval

    def test_sax(self):
        p = Paa(self.series)
        print(p(1000))
        sx = Sax(p(1000))
        print([i for i in sx("abcde")])

if __name__ == '__main__':
    unittest.main()
