from os import getenv
from flask import Flask, request, jsonify
from flask_api import status
# import obspy
#
from seismic.metadb import get_session, ObservationRecord

app = Flask(__name__)

MINIO_HOST = getenv("MINIO_HOST", "localhost:9000")
MINIO_ACCESS_KEY = getenv("MINIO_ACCESS_KEY", "dev-TKE8KC10YL")
MINIO_SECRET_KEY = getenv("MINIO_SECRET_KEY", "dev-ALUP1N7WUO")
MINIO_BUCKET = getenv("MINIO_BUCKET", "raw")
DB_URL = getenv("DB_URL", "postgresql://seismic:d3v3l0pm3nt!@localhost:5432/seismic")


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


@app.route("/search", methods=["GET"])
def search():
    s = get_session(DB_URL)

    if all(k in request.args for k in ("network", "station", "channel")):
        r = s.query(ObservationRecord)\
            .filter_by(**{k: request.args[k] for k in ("network", "station", "channel")})\
            .order_by(ObservationRecord.start)\
            .all()
        return jsonify([{
            "id": o.obs_id,
            "start": o.start.isoformat() + "Z",
            "end": o.end.isoformat() + "Z",
        } for o in r])
    elif all(k in request.args for k in ("network", "station")):
        r = s.query(ObservationRecord.channel)\
            .filter_by(**{k: request.args[k] for k in ("network", "station")})\
            .distinct().all()
    elif "network" in request.args:
        r = s.query(ObservationRecord.station)\
            .filter_by(network=request.args["network"]).distinct().all()
    else:
        r = s.query(ObservationRecord.network).distinct().all()
    return jsonify(r)


@app.route("/", methods=["GET"])
def get():
    # Check all required params are provided
    req_params = ("network", "station", "channel", "start", "end", "sampling_rate")
    missing_params = [p for p in req_params if p not in request.args]
    if len(missing_params) > 0:
        raise ErrorHandler("Missing Parameters: {}".format(", ".join(missing_params)))
    # DB Session
    s = get_session(DB_URL)
    q = s.query(ObservationRecord).filter(
        ObservationRecord.network == request.args["network"],
        ObservationRecord.station == request.args["station"],
        ObservationRecord.channel == request.args["channel"],
        ObservationRecord.sampling_rate == request.args["sampling_rate"],
        ObservationRecord.start <= request.args["start"],
        ObservationRecord.end >= request.args["end"],
    ).all()
    return str([i.__dict__ for i in q]), status.HTTP_200_OK

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=8002,
        debug=True
    )