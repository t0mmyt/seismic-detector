#!/usr/bin/env python3
import unittest
import numpy as np

from seismic.frequency.interpolator import zero_intersect, phase_inversions, frequency


class ZeroIntersect(unittest.TestCase):
    def test_neg_to_pos_intersect(self):
        self.assertEqual(zero_intersect(-1, 2, 6), 2)

    def test_pos_to_neg_intersect(self):
        self.assertEqual(zero_intersect(2, -1, 6), 4)


class PhaseInversions(unittest.TestCase):
    def test_phase_inversions(self):
        data = [-1, 1, -1, 1, -2, 2]
        interval = 1
        calculated = list(phase_inversions(data, interval))
        expected = [0.5, 1.5, 2.5, 3.333, 4.5]
        for i in range(len(calculated)):
            self.assertAlmostEqual(
                calculated[i], expected[i], 3,
                "Calculated != expected at pos {}".format(i))


class Frequency(unittest.TestCase):
    def test_check_calculated_frequencies(self):
        # Test frequency calculations for a Sine wave with cycles of 1 - 100Hz
        for f in range(1, 100):
            true_f = f
            t = np.array(range(10000))
            y = np.sin(2 * np.pi * (t / (1000 / true_f)))
            calc_f = list(frequency(y, 1))
            for i in range(len(calc_f)):
                self.assertAlmostEqual(
                    calc_f[i][1], true_f, 0,
                    "Calculated freq at {} was not {}".format(i, true_f)
                )
