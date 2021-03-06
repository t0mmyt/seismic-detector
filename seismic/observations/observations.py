"""
Library for reading SAC observations for import to a TSDB
"""
import obspy
from obspy.signal.filter import bandpass
import pandas as pd
import numpy as np
from iso8601 import parse_date
import datetime
import logging
import pytz
import json

from seismic.metadb import ObservationRecord
from io import BytesIO


log = logging.getLogger("observations")


def min_max(series):
    """
    Aggregation function to return either the max value if +ve or the min if -ve for use with Pandas resampling
     
    Args:
        series: window of data to aggregate on 

    Returns:
        min or max
    """
    mn = np.min(series)
    mx = np.max(series)
    return mx if mx > abs(mn) else mn


class ObservationDAOError(Exception):
    """
    Exception to contain all errors relating to loading the observations
    """
    pass


class ObservationDAO(object):
    ObservationDAOError = ObservationDAOError

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
            self.stream[0].data = self.stream[0].data.byteswap().newbyteorder()
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
        elif self.filename and len(self.filename) > 0 and self.filename[-1].upper() in ("Z", "N", "E"):
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
        log.debug("Obs Start: {}".format(datetime.datetime.fromtimestamp(self.stats.starttime.timestamp).timestamp()))
        return ObservationRecord(
            network=self.stats.network,
            station=self.stats.station,
            channel=self.stats.channel,
            start=datetime.datetime.fromtimestamp(self.stats.starttime.timestamp, pytz.UTC),
            end=datetime.datetime.fromtimestamp(self.stats.endtime.timestamp, pytz.UTC),
            format=self.stats._format,
            filename=self.filename,
            sampling_rate=self.stats.sampling_rate
        )

    def slice(self, start, end):
        """
        Perform an inplace obspy slice on the data to work on a smaller dataset.
        
        Args:
            start (float): Seconds since the epoch
            end (float): Seconds since the epoch 
        """
        self.stream = self.stream.slice(
            starttime=obspy.UTCDateTime(start),
            endtime=obspy.UTCDateTime(end))

    def normalise(self):
        x = self.stream[0].data
        self.stream[0].data = (x - x.mean()) / x.std()

    def absolute(self):
        x = self.stream[0].data
        self.stream[0].data = np.abs(x)

    def bandpass(self, low, high):
        self.stream[0].data = bandpass(self.stream[0].data, low, high, self.stream[0].meta.sampling_rate)

    def view(self, npts=2000):
        """
        Return downsampled graph data for rendering in the browser.

        Args:
            npts (int): number points to return

        Returns:
            JSON from Pandas DataFrame orientated by records
        """
        df = self.dataframe()
        duration = (df.index[-1] - df.index[0]) / np.timedelta64(1, "ms")
        log.info(duration)
        smpl = df.resample("{}L".format(int(duration / npts))).apply(min_max).interpolate(method='time')
        log.debug("Len: {}".format(len(smpl)))
        smpl["x"] = smpl.index.astype(np.int64) // 10 ** 6
        return json.loads(smpl.to_json(orient="records"))

    def dataframe(self):
        t = self.stream[0].copy()
        duration = (t.meta.endtime - t.meta.starttime) * 1000
        rng = pd.date_range(
            start=pd.to_datetime(
                parse_date(str(t.meta.starttime)).replace(tzinfo=pytz.UTC).timestamp() * 1000, unit="ms"),
            end=pd.to_datetime(
                parse_date(str(t.meta.endtime)).replace(tzinfo=pytz.UTC).timestamp() * 1000, unit="ms"),
            freq=("{}U".format(int(10 ** 3 * duration / (t.meta.npts - 1))))
        )
        y = t.data
        return pd.DataFrame({"y": y}, index=rng)

    def series(self):
        df = self.dataframe()
        return pd.Series(data=df["y"], index=df.index)

    def write(self, fmt="SAC"):
        b = BytesIO()
        self.stream.write(b, format=fmt)
        b.seek(0)
        return b

