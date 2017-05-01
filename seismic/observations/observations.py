"""
Library for reading SAC observations for import to a TSDB
"""
import obspy
import pandas as pd
import numpy as np
from iso8601 import parse_date
import logging
import pytz
import json

from seismic.metadb import ObservationRecord


log = logging.getLogger("observations")


def min_max(series):
    # assert isinstance(series, np.ndarray), "series should be an ndarray, got {}".format(type(series))
    mn = np.min(series)
    mx = np.max(series)
    return mx if mx > abs(mn) else mn


class ObservationDAOError(Exception):
    """
    Exception to contain all errors relating to loading the observations
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ObservationDAO(object):
    def __init__(self, path, filename=None):
        """
        Read an obspy compatible file (e.g. SAC, miniseed) and return a payload
        for insertion in to a TSDB.

        Args:
            path: path to the file or BytesIO object.
        """
        try:
            self.stream = obspy.core.stream.read(path)
            self.filename = filename
            log.debug("Read {}".format(filename))
        except (IOError, TypeError) as e:
            raise ObservationDAOError('Failed to read {}: {}'.format(path, e))

    @property
    def trace_count(self):
        """
        How many traces in the trace

        Returns:
            int
        """
        return len(self.stream)

    # TODO - Break this up, don't figure out variables twice
    @property
    def stats(self, trace=0):
        """
        Get metadata from a trace.
        
        Args:
            trace: int

        Returns:
            Dict
        """
        trace = self.stream[trace]
        stats = trace.stats
        if len(stats["network"]) == 0:
            stats["network"] = "Unknown"
        if len(stats["channel"]) > 0:
            stats["channel"] = stats['channel'][-1]
        elif len(self.filename) > 0 and self.filename[-1].upper() in ("Z", "N", "E"):
            stats["channel"] = self.filename[-1].upper()
        else:
            stats["channel"] = "?"
        return stats
    
    def observation_record(self):
        """
        Create an ObservationRecord for insertion in to database.
        
        Returns:
            ObservationRecord
        """
        return ObservationRecord(
            network=self.stats.network,
            station=self.stats.station,
            channel=self.stats.channel,
            start=parse_date(str(self.stats.starttime)),
            end=parse_date(str(self.stats.endtime)),
            format=self.stats._format,
            filename=self.filename,
            sampling_rate=self.stats.sampling_rate
        )

    def view(self):
        t = self.stream[0].copy()
        duration = (t.meta.endtime - t.meta.starttime)
        rng = pd.date_range(
            start=pd.to_datetime(
                parse_date(str(t.meta.starttime)).replace(tzinfo=pytz.UTC).timestamp() * 1000, unit="ms"),
            end=pd.to_datetime(
                parse_date(str(t.meta.endtime)).replace(tzinfo=pytz.UTC).timestamp() * 1000, unit="ms"),
            freq=("{}U".format(int(10 ** 6 * duration / (t.meta.npts - 1))))
        )
        y = t.data
        y = y.byteswap().newbyteorder()
        df = pd.DataFrame({"y": y}, index=rng)
        log.debug("Duration: {}".format(duration))
        smpl = df.resample("{}L".format(int(duration / 2))).apply(min_max)
        log.debug("Len: {}".format(len(smpl)))
        smpl["t"] = smpl.index.astype(np.int64) // 10 ** 6
        return json.loads(smpl.to_json(orient="records"))
