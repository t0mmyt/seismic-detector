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
    title='SAX API',
    description='(Mostly) Restful API for doing SAX'
)
sax_ns = api.namespace("sax")  # TODO Description


@sax_ns.route("/<evt_id>/view")
class View(Resource):
    def get(self, evt_id):
        try:
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            db = get_session(DB_URL)
            evt = db.query(EventRecord).filter_by(evt_id=evt_id).one()
            raw = ds.get(evt.obs_id)
            obs = ObservationDAO(raw)
            obs.slice(
                start=evt.start.timestamp(),
                end=evt.end.timestamp()
            )
            return obs.view()
        except NoResultFound:
            return None, status.HTTP_404_NOT_FOUND
        except MultipleResultsFound:
            raise InternalServerError("Multiple results found, this is bad")
        except DatastoreError as e:
            raise InternalServerError(e)

if __name__ == "__main__":
    app.logger.setLevel(logging.DEBUG)
    app.run(
        host="0.0.0.0",
        port=8001,
        debug=True,
    )