import unittest

from seismic.observations import ObservationDAO
from seismic.detector import SaxDetect, StaLtaDetect
from seismic.detector.sax import sax_detect


def gen_from_string(ss):
    for s in ss:
        yield s


class SaxDetectTest(unittest.TestCase):
    def setUp(self):
        self.paa_int = 50  # ms of intervals for following samples
        self.alphabet = "abcdefg"  # alphabet for following samples

        self.sax_str_1 = (
            "ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
            "dddddddddddddddddddddddddddddddddacgagdbabbgcgagebgabgfagddbcbgfgac"
            "ecfgabgadagaebggeggaadgaagadgfaadggbafggabaefgabgeabgaafgefgbdbbbag"
            "ggfeaecaadgggffbbbdccdgeddeaacdffecccbdfdefcbcbbegfdcccddeedbceeefd"
            "dceeddeefdecbddddeeddcddeccdeeccddeddeeddccbdddccdcdddefdccdcdeeddd"
            "cdedededdeeedccdddeedddccccddddddccddccddddddcddcddddeedddccdedcddc"
            "cddddddddddddeeedeeddcddddddddddddddddddddddddddddedddddddddddddddd"
            "ddddddddcccdddddddddddddddddddddedddddddddddddddddddddddddddddddddd"
            "dddddddddddcccdcddddddddddddddddddddddddddddddddddddddddddddddddd")

        self.sax_str_2 = (
            "ddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
            "ddddddddddddddddddddddddddddddddfgacaaggaadggaabcgadbfeaffdbebfebbf"
            "feecbcfebedgbddedccegdbbbffceccddeecfacfgebggcaggaaeggaagfacedeagea"
            "gfgaegbaefgeeaaggbaaagfcbfecffeacefcbgbddbeadgdddeedebddbddaeedfbef"
            "gdccacccegfcdcdfdeeffdcbaadegeecaccdffecdeedeeccbbcceeeddddedcdeddc"
            "ceecdeddedcdeedcbeddddcdddddeecdeecdddcbeeddddddeedccdeddeddddddddd"
            "cccdddeddeeddddcbcdedcddddccdddeddddeedddedddeedddddcdccdeedddedddd"
            "dcccdddddddddddcdddedeedddcdeedccdddddeedddddddddddddddddddddcddddd"
            "ddddddddddddddddddddddddccdddddddddddcdddddddddddddeddddddeeedddd")

    def test_sax_detect(self):
        """
        Tests two known events using sax_detect algorithm with a minimum event length of 5s to
        trigger on and a minimum quiet period of 5s to trigger off.

        These are Unknown.CALZ and Unknown.CAOZ respectively.
        """
        # String 1
        t = list(sax_detect(gen_from_string(self.sax_str_1), self.alphabet, self.paa_int, 5000, 5000))
        self.assertEqual(len(t), 1, "Only one event should be found")
        duration_ms = (t[0][1] - t[0][0])
        self.assertTrue(10000 <= duration_ms <= 15000, "Event was between 8 and 15 seconds, got {}".format(duration_ms))
        self.assertAlmostEqual(t[0][0] / 1000, 5, 1, "Event was approximately 5000ms from the start, got {}".format(t[0][0]))
        # String 2
        t = list(sax_detect(gen_from_string(self.sax_str_2), self.alphabet, self.paa_int, 5000, 5000))
        self.assertEqual(len(t), 1, "Only one event should be found")
        duration_ms = (t[0][1] - t[0][0])
        self.assertTrue(10000 <= duration_ms <= 20000, "Event was between 10 and 20 seconds, got {}".format(duration_ms))
        self.assertAlmostEqual(t[0][0] / 1000, 5, 1, "Event was approximately 5000ms from the start, got {}".format(t[0][0]))

    def test_full_sax_detector_class_1(self):
        o = ObservationDAO("../../sample/_all/cal.z")
        o.bandpass(5, 10)
        det = SaxDetect(o.stream[0].data, o.stats.sampling_rate)
        s, e = det.detect(self.alphabet, self.paa_int).__next__()
        self.assertTrue((10.5 <= s / 1000 <= 11), "Event start was 10.5 to 11 seconds from start, got {}".format(s / 1000))
        self.assertTrue((20.0 <= e / 1000 <= 30.0), "Event end was 20 to 30 seconds from start, got {}".format(e / 1000))

    def test_full_sax_detector_class_2(self):
        o = ObservationDAO("../../sample/_all/cao.z")
        o.bandpass(5, 10)
        det = SaxDetect(o.stream[0].data, o.stats.sampling_rate)
        s, e = det.detect(self.alphabet, self.paa_int).__next__()
        self.assertTrue((11.5 <= s / 1000 <= 12.5), "Event start was 11.5 to 12.5 seconds from start, got {}".format(s / 1000))
        self.assertTrue((25.0 <= e / 1000 <= 35.0), "Event end was 20 to 30 seconds from start, got {}".format(e / 1000))

    def test_full_sax_detector_class_3(self):
        o = ObservationDAO("../../sample/_all/cps.z")
        o.bandpass(5, 10)
        det = SaxDetect(o.stream[0].data, o.stats.sampling_rate)
        s, e = det.detect(self.alphabet, self.paa_int).__next__()
        self.assertTrue((11.5 <= s / 1000 <= 12.5), "Event start was 11.5 to 12.5 seconds from start, got {}".format(s / 1000))
        # self.assertTrue((25.0 <= e / 1000 <= 35.0), "Event end was 20 to 30 seconds from start, got {}".format(e / 1000))

    def test_full_stalta_detector_class_1(self):
        o = ObservationDAO("../../sample/_all/cal.z")
        o.bandpass(5, 10)
        det = StaLtaDetect(o.stream[0].data, o.stats.sampling_rate)
        s, e = det.detect(short=50, long=5000, nstds=3, trigger_len=5000).__next__()
        self.assertTrue((10.5 <= s / 1000 <= 11), "Event start was 10.5 to 11 seconds from start, got {}".format(s / 1000))
        self.assertTrue((20.0 <= e / 1000 <= 30.0), "Event end was 25 to 35 seconds from start, got {}".format(e / 1000))

    def test_full_stalta_detector_class_2(self):
        o = ObservationDAO("../../sample/_all/cao.z")
        o.bandpass(5, 10)
        det = StaLtaDetect(o.stream[0].data, o.stats.sampling_rate)
        s, e = det.detect(short=50, long=5000, nstds=3, trigger_len=5000).__next__()
        self.assertTrue((11.5 <= s / 1000 <= 12.5), "Event start was 11.5 to 12.5 seconds from start, got {}".format(s / 1000))
        self.assertTrue((25.0 <= e / 1000 <= 35.0), "Event end was 25 to 35 seconds from start, got {}".format(e / 1000))

