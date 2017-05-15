from os import getenv
from io import BytesIO
import logging
import pandas as pd
import numpy as np
import pytz
import json
from flask import Flask, request, send_file
from flask_api import status
from flask_restplus import Api, Resource, reqparse
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


def is_true(s=str):
    """
    Checks if a string sounds truth-y (e.g. from a url encoded string)
    Args:
        s (string): string to check

    Returns:
        Boolean
    """
    return s.lower() in ["true", "yes", "y", "1"] if s else False


@sax_ns.route("/<evt_id>/view")
@sax_ns.param("absolute", "Work on absolute values", type="boolean")
@sax_ns.param("bandpass", "Whether or not to perform a bandpass filter", type="boolean")
@sax_ns.param("bandpassLow", "Low frequency (Hz) for bandpass", type="integer")
@sax_ns.param("bandpassHigh", "High frequency (Hz) for bandpass", type="integer")
@sax_ns.param("sax", "Whether or not to perform SAX construction", type="boolean")
@sax_ns.param("paaInt", "PAA Interval for SAX", type="boolean")
@sax_ns.param("alphabet", "Alphabet for SAX", type="boolean")
class View(Resource):
    def get(self, evt_id):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("absolute", type=str)
            parser.add_argument("bandpass", type=str)
            parser.add_argument("bandpassLow", type=int)
            parser.add_argument("bandpassHigh", type=int)
            parser.add_argument("sax", type=str)
            parser.add_argument("paaInt", type=int)
            parser.add_argument("alphabet", type=str)
            p = parser.parse_args()
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            db = get_session(DB_URL)
            evt = db.query(EventRecord).filter_by(evt_id=evt_id).one()
            raw = ds.get(evt.obs_id)
            obs = ObservationDAO(raw)
            obs.slice(
                start=evt.start.timestamp(),
                end=evt.end.timestamp()
            )
            obs.normalise()
            if is_true(p["bandpass"]):
                obs.bandpass(p["bandpassLow"], p["bandpassHigh"])
            if is_true(p["absolute"]):
                obs.absolute()
            return obs.view()
        except NoResultFound:
            raise NotFound
        except MultipleResultsFound:
            raise InternalServerError("Multiple results found, this is bad")
        except DatastoreError as e:
            raise InternalServerError(e)

if __name__ == "__main__":
    app.logger.setLevel(logging.INFO)
    app.run(
        host="0.0.0.0",
        port=8001,
        debug=True,
    )