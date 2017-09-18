import types
from collections import deque
import pandas as pd
import numpy as np

from seismic.sax import Paa, PaaError, Sax, SaxError
from .utils import make_series
from .detectorbase import DetectorBase
from .exceptions import DetectorError


class SaxDetectWindow(DetectorBase):
    def detect(self, alphabet, paa_int, buffer_len, threshold, window_size_ms):
        if not len(alphabet) % 2 == 1:
            raise DetectorError(
                "SaxDetect requires an odd length of alphabet to have a centre")

        centre = alphabet[int(len(alphabet) / 2)]
        max_from_centre = 1
        buffer_len = int(buffer_len / paa_int)

        def near_centre(s):
            return s == centre or abs(alphabet.find(centre) - alphabet.find(s)) <= max_from_centre

        def sax_detect_window(start, end):
            print(".")
            nonlocal triggered
            paa_win = Paa(make_series(self.trace[start:end], self.freq))
            sax_win = Sax(paa_win(paa_int))
            j = 0
            trigger_threshold = int((buffer_len + 0.5) // 2)
            buffer = deque(np.ndarray(buffer_len, dtype=bool), maxlen=buffer_len)
            ss = deque([], maxlen=buffer_len)
            for s in sax_win(alphabet):
                buffer.append(near_centre(s))
                ss.append(s)
                if j >= buffer_len:
                    if not triggered and sum(buffer) < trigger_threshold:
                        b = list(buffer)
                        if sum(b[:trigger_threshold]) > sum(b[trigger_threshold:]):
                            print(ss)
                            triggered = True
                            yield triggered, j - len(buffer) + trigger_threshold
                    elif triggered and sum(buffer) > trigger_threshold:
                        # print("off", "".join(ss))
                        triggered = False
                        yield triggered, j - len(buffer) + trigger_threshold
                j += 1

        window = int(window_size_ms // self.interval)
        half_window = int(window // 2)
        last = len(self.trace) - 1
        i = 0
        t_on_i = None
        triggered = False
        while i < last:
            end_pos = min(last, i + half_window)
            for t_on, pos in sax_detect_window(i, end_pos):
                print(i, pos)
                real_pos = pos + i
                if t_on:
                    t_on_i = real_pos
                elif not t_on and t_on_i and real_pos - t_on_i > (threshold / paa_int):
                    yield t_on_i * paa_int, real_pos * paa_int

            i += int(window / 2)
