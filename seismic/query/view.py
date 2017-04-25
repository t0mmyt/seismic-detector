from os import getenv
from iso8601 import parse_date
import numpy as np
import pandas as pd
import pytz

from seismic.datastore import Datastore, DatastoreError
from seismic.obsloader import Observation, ObservationError


# TODO - needed here?
MINIO_HOST = getenv("MINIO_HOST", "localhost:9000")
MINIO_ACCESS_KEY = getenv("MINIO_ACCESS_KEY", "dev-TKE8KC10YL")
MINIO_SECRET_KEY = getenv("MINIO_SECRET_KEY", "dev-ALUP1N7WUO")
MINIO_BUCKET = getenv("MINIO_BUCKET", "raw")
DB_URL = getenv("DB_URL", "postgresql://seismic:d3v3l0pm3nt!@localhost:5432/seismic")


class ViewError(Exception):
    pass


# class ViewPayload(dict):
#     __dict__ = {}
#
#     @property
#     def start(self):
#         return


class View(object):
    def __init__(self, obs_id):
        try:
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            self.o = Observation(ds.get(obs_id))
        except DatastoreError as e:
            raise ViewError("Datastore error: {}".format(str(e)))
        except ObservationError as e:
            raise ViewError("Observation error: {}".format(str(e)))

    def original(self, trace=0):
        """
        Return raw data from observation file
        
        Args:
            trace: trace number in file (default 0) 

        Returns:
            dict
        """
        t = self.o.stream[trace]
        return {
            "meta": {
                "network": t.meta.network,
                "station": t.meta.station,
                "channel": t.meta.channel[-1:],
                "sampling_rate": t.meta.sampling_rate,
            },
            "start": parse_date(str(t.meta.starttime)).replace(tzinfo=pytz.UTC).timestamp() * 1000,
            "end": parse_date(str(t.meta.endtime)).replace(tzinfo=pytz.UTC).timestamp() * 1000,
            "interval": 1000.0 / t.meta.sampling_rate,
            "datapoints": t.data.tolist()
        }

    def downsampled(self, ms=100):
        orig = self.original()
        rng = pd.date_range(
            start=pd.to_datetime(orig['start'], unit="ms"),
            end=pd.to_datetime(orig['end'], unit="ms"),
            freq=("{}L".format(int(orig['interval']))),
        )
        df = pd.DataFrame({"y": orig['datapoints']}, index=rng)
        # downsampled = df.asfreq("{}L".format(int(ms)))
        # downsampled["t"] = downsampled.index.astype(np.int64) // 10 ** 6
        d = df.to_dict("rows")
        return d
