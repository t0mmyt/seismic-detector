from os import getenv
from flask import Flask, request, send_file, jsonify, Response
from flask_api import status
import matplotlib.pyplot as plt

from seismic.datastore import Datastore, DatastoreError
from seismic.metadb import get_session, ObservationRecord, EventRecord
from seismic.query.view import View, ViewError

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
        evt_counts = {}
        for o in r:
            evt_counts[o.obs_id] = \
                s.query(EventRecord).filter(EventRecord.obs_id == o.obs_id).count()
        return jsonify([{
            "id": o.obs_id,
            "start": o.start.isoformat() + "Z",
            "end": o.end.isoformat() + "Z",
            "sampling_rate": o.sampling_rate,
            "events": evt_counts[o.obs_id]
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


@app.route("/events/<obs_id>", methods=["GET"])
def events(obs_id):
    # TODO - Exceptions
    s = get_session(DB_URL)
    r = s.query(EventRecord).\
        filter_by(obs_id=obs_id).\
        order_by(EventRecord.start).\
        all()
    return jsonify([{
        "evt_id": e.evt_id,
        "obs_id": e.obs_id,
        "start": e.start.isoformat() + "Z",
        "end": e.end.isoformat() + "Z",
        "duration": int((e.end - e.start).total_seconds() * 1000)
    } for e in r])


@app.route("/<obs_id>", methods=["GET", "DELETE"])
def get(obs_id):
    events_only = True if request.args.get("eventsOnly") == "true" else False
    ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
    if request.method == "DELETE":
        try:
            # Delete DB entry
            s = get_session(DB_URL)
            s.query(EventRecord).filter(EventRecord.obs_id == obs_id).delete()
            if not events_only:
                s.query(ObservationRecord).filter(ObservationRecord.obs_id == obs_id).delete()
                # Delete Object
                ds.delete(obs_id)
            # Commit DB if all went well
            s.commit()
            return '', status.HTTP_204_NO_CONTENT
        except DatastoreError as e:
            raise ErrorHandler(e, 500)
    elif request.method == "GET":
        try:
            data = ds.get(obs_id)
            return send_file(data, mimetype="application/octet")
        except DatastoreError as e:
            raise ErrorHandler(e, 500)
    else:
        raise ErrorHandler("{} not implemented.".format(request.method))


@app.route("/event/thumbnail/<obs_id>/<evt_id>.png")
def evt_thumbnail(obs_id, evt_id):
    ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
    img = ds.get("thumbails/{}/{}".format(obs_id, evt_id))
    return Response(img.read(), mimetype="image/png")


@app.route("/view/<obs_id>")
def view(obs_id):
    try:
        v = View(obs_id)
        return jsonify(v.original())
    except ViewError as e:
        raise ErrorHandler(e)


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=8002,
        debug=True
    )