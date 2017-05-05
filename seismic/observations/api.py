from os import getenv
from io import BytesIO
import logging
import pandas as pd
import numpy as np
import pytz
import json
from flask import Flask, request, send_file
from flask_api import status
from flask_restplus import Api, Resource, fields
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from seismic.observations.observations import ObservationDAO, ObservationDAOError
from seismic.datastore import Datastore, DatastoreError
from seismic.metadb.db import get_session, ObservationRecord, EventRecord

MINIO_HOST = getenv("MINIO_HOST", "localhost:9000")
MINIO_ACCESS_KEY = getenv("MINIO_ACCESS_KEY", "dev-TKE8KC10YL")
MINIO_SECRET_KEY = getenv("MINIO_SECRET_KEY", "dev-ALUP1N7WUO")
MINIO_BUCKET = getenv("MINIO_BUCKET", "raw")
DB_URL = getenv("DB_URL", "postgresql://seismic:d3v3l0pm3nt!@localhost:5432/seismic")

app = Flask("observations")
api = Api(
    app,
    version='1.0',
    title='Observations API',
    description='(Mostly) Restful API for storing and accessing observations and events'
)
obs_ns = api.namespace("observations")  # TODO Description


@obs_ns.route("/")
class Observations(Resource):
    def post(self):
        try:
            if request.headers.get("Content-Type", None) != "application/octet":
                raise BadRequest("Content-Type should be application/octet")
            filename = request.args.get("filename", "", type=str)
            # Database connections
            db = get_session(DB_URL)
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            # Read data from request
            data = BytesIO(request.data)
            obs = ObservationDAO(data, filename)
            obs_rec = obs.observation_record()
            db.add(obs_rec)
            ds.put(obs_rec.obs_id, data, data.getbuffer().nbytes)
            app.logger.info("Stored {} as {}".format(obs_rec.filename, obs_rec.obs_id))
            db.commit()
            return {"status": "ok", "obs_id": obs_rec.obs_id}, status.HTTP_201_CREATED
        except ObservationDAOError as e:
            raise BadRequest(e)
        except DatastoreError as e:
            raise InternalServerError("Datastore Error: {}".format(e))


@obs_ns.route("/<obs_id>")
class Observation(Resource):
    def get(self, obs_id):
        ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
        db = get_session(DB_URL)
        try:
            obs_rec = db.query(ObservationRecord).filter_by(obs_id=obs_id).one()
            filename = obs_rec.filename if len(obs_rec.filename) > 0 else obs_id
            data = ds.get(obs_id)
            return send_file(
                data,
                as_attachment=True,
                attachment_filename=filename,
                mimetype="application/octet"
            )
        except (DatastoreError, MultipleResultsFound) as e:
            raise InternalServerError(e)
        except NoResultFound:
            raise NotFound("{} not found".format(obs_id))

    def delete(self, obs_id):
        try:
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            db = get_session(DB_URL)
            events_only = True if request.args.get("eventsOnly") == "true" else False
            # Delete DB entry
            db.query(EventRecord).filter(EventRecord.obs_id == obs_id).delete()
            if not events_only:
                db.query(ObservationRecord).filter(ObservationRecord.obs_id == obs_id).delete()
                # Delete Object
                ds.delete(obs_id)
            # Commit DB if all went well
            db.commit()
            return "", status.HTTP_204_NO_CONTENT
        except DatastoreError as e:
            raise InternalServerError(e)


@obs_ns.route("/<obs_id>/view")
class View(Resource):
    def get(self, obs_id):
        try:
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            o = ObservationDAO(ds.get(obs_id))
            ov = o.view()
            app.logger.debug(ov)
            return o.view()
        except DatastoreError as e:
            raise InternalServerError(e)


@obs_ns.route("/<obs_id>/events")
class Events(Resource):
    def get(self, obs_id):
        # TODO - Exceptions
        db = get_session(DB_URL)
        r = db.query(EventRecord).\
            filter_by(obs_id=obs_id).\
            order_by(EventRecord.start).\
            all()
        return [{
            "evt_id": e.evt_id,
            "obs_id": e.obs_id,
            "start": e.start.replace(tzinfo=pytz.UTC).timestamp(),
            "end": e.end.replace(tzinfo=pytz.UTC).timestamp(),
            "duration": int((e.end - e.start).total_seconds() * 1000)
        } for e in r]


@obs_ns.route("/search")
class Search(Resource):
    def get(self):
        db = get_session(DB_URL)
        if all(k in request.args for k in ("network", "station", "channel")):
            r = db.query(ObservationRecord) \
                .filter_by(**{k: request.args[k] for k in ("network", "station", "channel")}) \
                .order_by(ObservationRecord.start) \
                .all()
            evt_counts = {}
            for o in r:
                evt_counts[o.obs_id] = \
                    db.query(EventRecord).filter(EventRecord.obs_id == o.obs_id).count()
            return [{
                "id": o.obs_id,
                "start": o.start.timestamp(),
                "end": o.end.timestamp(),
                "sampling_rate": o.sampling_rate,
                "filename": o.filename,
                "events": evt_counts[o.obs_id]
            } for o in r]
        elif all(k in request.args for k in ("network", "station")):
            r = db.query(ObservationRecord.channel) \
                .filter_by(**{k: request.args[k] for k in ("network", "station")}) \
                .distinct().all()
        elif "network" in request.args:
            r = db.query(ObservationRecord.station) \
                .filter_by(network=request.args["network"]).distinct().all()
        else:
            r = db.query(ObservationRecord.network).distinct().all()
            app.logger.debug(r)
        # return [i for j in r for i in j]  # Flatten r
        return r


@obs_ns.route("/<obs_id>/trigger_data")
class TriggerData(Resource):
    def get(self, obs_id):
        try:
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            db = get_session(DB_URL)
            obs_rec = db.query(ObservationRecord).filter_by(obs_id=obs_id).one()
            raw = ds.get("trigger_data/{}.json".format(obs_id))
            df = pd.read_json(raw)
            start_ms = obs_rec.start.timestamp() * 1000
            end_ms = obs_rec.end.timestamp() * 1000
            app.logger.info("Start: {}".format(start_ms))
            df["t"] = df["t"].add(start_ms)
            df["t"] = pd.to_datetime(df["t"], unit="ms")
            downsample_freq = int((end_ms - start_ms) / 1000)
            df.set_index("t", inplace=True)
            downsample = df.resample("{}L".format(downsample_freq)).mean()
            downsample["t"] = downsample.index.astype(np.int64) // 10 ** 6
            return json.loads(downsample.to_json(orient="records"))
        except DatastoreError as e:
            return str(e), status.HTTP_404_NOT_FOUND

if __name__ == "__main__":
    app.logger.setLevel(logging.DEBUG)
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,
    )
