import os
import re
import glob
from datetime import timedelta
from iso8601 import parse_date
import numpy as np
import obspy

line_re = re.compile("ALN_(\d{8}).(\d{6})\s+ALN_(\d{8}).(\d{6})")

def read_sims(filename):
    with open(filename, "r") as f:
        line = f.readline()
        while line:
            m = line_re.match(line)
            if m:
                g = m.groups()
                d1 = "{}-{}-{}T{}:{}:{}Z".format(
                    g[0][0:4], g[0][4:6], g[0][6:8], g[1][0:2], g[1][2:4], g[1][4:6])
                d2 = "{}-{}-{}T{}:{}:{}Z".format(
                    g[2][0:4], g[2][4:6], g[2][6:8], g[3][0:2], g[3][2:4], g[3][4:6])
                yield parse_date(d1), parse_date(d2)
            line = f.readline()


class SlicerError(Exception):
    pass


class Slicer(object):
    def __init__(self, basedir, network, station, channel):
        if not os.path.isdir(basedir):
            raise SlicerError("{} is not a directory".format(basedir))
        self.basedir = basedir
        self.network = network.upper()
        self.station = station.upper()
        self.channel = channel.upper()

    def get(self, start, duration=5000):
        d1 = obspy.UTCDateTime(start)
        d2 = obspy.UTCDateTime(start + timedelta(milliseconds=duration))
        obs_dir = os.path.join(self.basedir, d1.strftime("%Y.%j"))
        if not os.path.isdir(obs_dir):
            raise SlicerError("{} is not a directory".format(obs_dir))
        files = glob.glob(os.path.join(obs_dir, self.guess_file(d1)))
        if len(files) != 1:
            raise SlicerError("Did not match exactly one file: {}, {}".format(
                os.path.join(obs_dir, self.guess_file(d1)),
                files
            ))
        o = obspy.read(files[0])
        return o.slice(d1, d2)

    def guess_file(self, dt):
        return "{}.{}.{}..[BH]H{}.*.SAC".format(
            dt.strftime("%Y.%j.00.00.00.0000"),
            self.network,
            self.station,
            self.channel
        )


def remove_outlier(a):
    dist_from_mean = np.abs(a - np.mean(a))
    return np.delete(a, np.argmax(dist_from_mean))
