from io import BytesIO
import numpy as np
import pandas as pd
import pytz
import json
from datetime import timedelta
from flask import request, send_file, current_app as app
from flask_api import status
from flask_restplus import Namespace, Resource, reqparse
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from seismic.apis.env import *
from seismic.observations.observations import ObservationDAO, ObservationDAOError
from seismic.datastore import Datastore, DatastoreError
from seismic.metadb.db import get_session, ObservationRecord, EventRecord

api = Namespace("observations", description="Observations API")


@api.route("/")
class Observations(Resource):
    def post(self):
        """ Import an Observation file (in a format supported by Obspy) """
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


@api.route("/<obs_id>")
class Observation(Resource):
    def get(self, obs_id):
        """ Retrieve a RAW observation file """
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
        """ Delete an Observation """
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


@api.route("/<obs_id>/view")
class View(Resource):
    def get(self, obs_id):
        """ Return a Downsampled Observation for rendering graphically """
        try:
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            o = ObservationDAO(ds.get(obs_id))
            return o.view()
        except DatastoreError as e:
            raise InternalServerError(e)


@api.route("/<obs_id>/events")
class Events(Resource):
    def get(self, obs_id):
        """ List detected events for an Observation """
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


@api.route("/<obs_id>/<evt_id>")
@api.param("offset", "Offset start of event (ms)", type="integer")
@api.param("length", "Length of event", type="integer", required=True)
@api.param("filename", "Optional filename for downlaoded file", type="string")
class Event(Resource):
    def get(self, obs_id, evt_id):
        """ Retrieve a SAC file for an event """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("offset", type=int, default=0)
            parser.add_argument("length", type=int)
            parser.add_argument("filename", type=str)
            p = parser.parse_args()
            # Get observation
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            db = get_session(DB_URL)
            evt = db.query(EventRecord).filter_by(obs_id=obs_id, evt_id=evt_id).one()
            obs = ObservationDAO(ds.get(obs_id))
            # Slice event from observation
            start = (evt.start + timedelta(milliseconds=p["offset"]))
            if p["length"]:
                end = (start + timedelta(milliseconds=p["length"]))
            else:
                end = evt.end
            obs.slice(start.timestamp(), end.timestamp())
            # Prepare download
            filename = p["filename"] if p["filename"] else "{}.SAC".format(evt_id)
            b = BytesIO()
            obs.stream.write(b, format="SAC")
            b.seek(0)
            return send_file(
                b,
                as_attachment=True,
                attachment_filename=filename,
                mimetype="application/octet"
            )
        except NoResultFound:
            raise NotFound
        except MultipleResultsFound:
            raise InternalServerError("Multiple results found, this is bad")
        except DatastoreError as e:
            raise InternalServerError(e)


@api.route("/search")
class Search(Resource):
    def get(self):
        """ Search for stored Observations """
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
                "network": o.network,
                "station": o.station,
                "channel": o.channel,
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


@api.route("/<obs_id>/trigger_data")
class TriggerData(Resource):
    def get(self, obs_id):
        """ Return the trigger data for Event Detection on an Observation """
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
