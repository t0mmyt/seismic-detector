from os import getenv
from io import BytesIO
from flask import Flask, request, jsonify
from flask_api import status
from minio import Minio, ResponseError
from iso8601 import parse_date

from seismic.datastore import Datastore, DatastoreError
from seismic.metadb import ObservationRecord, get_session
from obs import *

app = Flask(__name__)
MINIO_HOST = getenv("MINIO_HOST", "localhost:9000")
MINIO_ACCESS_KEY = getenv("MINIO_ACCESS_KEY", "dev-TKE8KC10YL")
MINIO_SECRET_KEY = getenv("MINIO_SECRET_KEY", "dev-ALUP1N7WUO")
MINIO_BUCKET = getenv("MINIO_BUCKET", "raw")
DB_URL = "postgresql://seismic:d3v3l0pm3nt!@localhost:5432/seismic"


class ErrorHandler(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = str(message)
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(ErrorHandler)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/', methods=["POST"])
def receive():
    """
    Flask receiver for raw Observation files
    
    Returns:
        204 No Content if Ok
        400/500 on Error
    """
    try:
        # Check we have binary data
        if request.headers.get("Content-Type", None) != "application/octet":
            raise ErrorHandler("Content-Type should be application/octet")
        # Store data as a BytesIO and attempt to read as an Observation
        data = BytesIO(request.data)
        o = Observation(data)
        stats = o.stats()
        # Get DB session
        s = get_session(DB_URL)
        # Prepare ObservationRecord
        ObsRec = ObservationRecord(
            network=stats.network,
            station=stats.station,
            channel=stats.channel,
            start=parse_date(str(stats.starttime)),
            end=parse_date(str(stats.endtime)),
            format=stats._format,
            sampling_rate=stats.sampling_rate
        )
        # Add Record to MetaDB
        s.add(ObsRec)
        # Send to Datastore
        ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
        ds.put(ObsRec.obs_id, data, data.getbuffer().nbytes)
        s.commit()
        return "", status.HTTP_204_NO_CONTENT
    except ObservationError as e:
        raise ErrorHandler(e, 400)
    except DatastoreError as e:
        raise ErrorHandler(e, 500)


if __name__ == '__main__':
    app.run(debug=True)