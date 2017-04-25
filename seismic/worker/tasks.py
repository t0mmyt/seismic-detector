from os import getenv
from celery import Celery
import logging
from logging import error, info
import obspy
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
import pytz
from datetime import timedelta

from seismic.datastore import Datastore, DatastoreError
from seismic.metadb import get_session, ObservationRecord, EventRecord
from seismic.detector import Detector, DetectorError

MINIO_HOST = getenv("MINIO_HOST", "localhost:9000")
MINIO_ACCESS_KEY = getenv("MINIO_ACCESS_KEY", "dev-TKE8KC10YL")
MINIO_SECRET_KEY = getenv("MINIO_SECRET_KEY", "dev-ALUP1N7WUO")
MINIO_BUCKET = getenv("MINIO_BUCKET", "raw")
DB_URL = getenv("DB_URL", "postgresql://seismic:d3v3l0pm3nt!@localhost:5432/seismic")
BROKER_URL = getenv("BROKER_URL", "redis://localhost:6379")

capp = Celery('tasks', broker=BROKER_URL)
ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@capp.task()
def detector(obs_id, trace, bp_low, bp_high, short_window, long_window, nstds, trigger_len):
    """
    Run detector to find events and store in metadb
    
    Args:
        obs_id (string): Observation ID
        trace (int): Number of trace in file (probably 0)
        bp_low (int): Low frequency for bandpass
        bp_high (int): High frequency for bandpass 
        short_window (int): Length of short window in ms
        long_window (int): Length of long window in ms
        nstds (int): Number of standard deviations for trigger
        trigger_len: minimum length in ms of short mean observations being above nstds to trigger

    Returns:

    """
    try:
        raw = ds.get(obs_id)
        o = obspy.read(raw)
        t = o[trace]
        d = Detector(t.data, t.meta.sampling_rate)
        d.bandpass(bp_low, bp_high)
        s = get_session(DB_URL)
        obs_rec = s.query(ObservationRecord).\
            filter_by(obs_id=obs_id).one()
        start_time = obs_rec.start.replace(tzinfo=pytz.UTC)
        for evt in d.detect(short_window, long_window, nstds, trigger_len):
            er = EventRecord(
                obs_id=obs_id,
                network=obs_rec.network,
                station=obs_rec.station,
                channel=obs_rec.channel,
                start=start_time + timedelta(milliseconds=evt[0]),
                end=start_time + timedelta(milliseconds=evt[1]),
                sampling_rate=obs_rec.sampling_rate
            )
            s.add(er)
        s.commit()
    except (DatastoreError, DetectorError) as e:
        error(str(e))
    except (NoResultFound, MultipleResultsFound) as e:
        error("No single result from DB: {}".format(e))