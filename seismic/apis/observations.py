from io import BytesIO
from flask import request, current_app as app
from flask_api import status
from flask_restplus import Namespace, Resource, fields
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from seismic.api.env import *
from seismic.observations.observations import ObservationDAO, ObservationDAOError
from seismic.datastore import Datastore, DatastoreError
from seismic.metadb.db import get_session, ObservationRecord, EventRecord

api = Namespace("observations", description="Observations API")


api.route("/")
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
