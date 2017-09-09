from datetime import timedelta
import json
from flask import request, send_file, current_app as app
from flask_restplus import Namespace, Resource, fields, reqparse
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from seismic.apis.env import *
from seismic.apis.utils import is_true
from seismic.observations.observations import ObservationDAO, ObservationDAOError
from seismic.datastore import Datastore, DatastoreError
from seismic.metadb.db import get_session, ObservationRecord, EventRecord
from seismic.sax import Paa, PaaError, Sax, SaxError
api = Namespace("sax", description="PAA/SAX API")


@api.route("/event/<evt_id>/view")
@api.param("offset", "Offset start of event (ms)", type="integer")
@api.param("length", "Length of event", type="integer", required=True)
@api.param("absolute", "Work on absolute values", type="boolean")
@api.param("bandpass", "Whether or not to perform a bandpass filter", type="boolean")
@api.param("bandpassLow", "Low frequency (Hz) for bandpass", type="integer")
@api.param("bandpassHigh", "High frequency (Hz) for bandpass", type="integer")
# @api.param("sax", "Whether or not to perform SAX construction", type="boolean")
@api.param("paaInt", "PAA Interval for SAX", type="integer", required=True)
@api.param("alphabet", "Alphabet for SAX", type="string", required=True)
class SaxEvent(Resource):
    def get(self, evt_id):
        """ Return SAX data for a detected Event """
        try:
            parser = reqparse.RequestParser()
            parser.add_argument("offset", type=int, default=0)
            parser.add_argument("length", type=int, required=True)
            parser.add_argument("absolute", type=str)
            parser.add_argument("bandpass", type=str)
            parser.add_argument("bandpassLow", type=int)
            parser.add_argument("bandpassHigh", type=int)
            parser.add_argument("sax", type=str)
            parser.add_argument("paaInt", type=int, required=True)
            parser.add_argument("alphabet", type=str, required=True)
            p = parser.parse_args()
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            db = get_session(DB_URL)
            evt = db.query(EventRecord).filter_by(evt_id=evt_id).one()
            raw = ds.get(evt.obs_id)
            obs = ObservationDAO(raw)
            start = (evt.start + timedelta(milliseconds=p["offset"]))
            end = (start + timedelta(milliseconds=p["length"]))
            obs.slice(
                start=start.timestamp(),
                end=end.timestamp()
            )
            obs.normalise()
            if is_true(p["bandpass"]):
                obs.bandpass(p["bandpassLow"], p["bandpassHigh"])
            if is_true(p["absolute"]):
                obs.absolute()
            paa = Paa(obs.series())
            paa_data = paa(p["paaInt"])
            paa_results = [{"x": int(k), "y": v} for k, v in json.loads(paa_data.to_json(orient="index")).items()]
            paa_results = sorted(paa_results, key=lambda x: x["x"])
            sax = Sax(paa_data)
            return {
                "original": obs.view(),
                "paa": paa_results,
                "sax": "".join([i for i in sax(p["alphabet"])])
            }
        except (PaaError, SaxError) as e:
            raise InternalServerError(e)
        except NoResultFound:
            raise NotFound
        except MultipleResultsFound:
            raise InternalServerError("Multiple results found, this is bad")
        except DatastoreError as e:
            raise InternalServerError(e)


@api.route("/observation/<obs_id>/view")
# @api.param("offset", "Offset start of event (ms)", type="integer")
# @api.param("length", "Length of event", type="integer", required=True)
@api.param("absolute", "Work on absolute values", type="boolean")
@api.param("bandpass", "Whether or not to perform a bandpass filter", type="boolean")
@api.param("bandpassLow", "Low frequency (Hz) for bandpass", type="integer")
@api.param("bandpassHigh", "High frequency (Hz) for bandpass", type="integer")
# @api.param("sax", "Whether or not to perform SAX construction", type="boolean")
@api.param("paaInt", "PAA Interval for SAX", type="integer", required=True)
@api.param("alphabet", "Alphabet for SAX", type="string", required=True)
class SaxObservation(Resource):
    def get(self, obs_id):
        """ Return SAX data for a whole Observation """
        try:
            parser = reqparse.RequestParser()
            # parser.add_argument("offset", type=int, default=0)
            # parser.add_argument("length", type=int, required=True)
            parser.add_argument("absolute", type=str)
            parser.add_argument("bandpass", type=str)
            parser.add_argument("bandpassLow", type=int)
            parser.add_argument("bandpassHigh", type=int)
            parser.add_argument("sax", type=str)
            parser.add_argument("paaInt", type=int, required=True)
            parser.add_argument("alphabet", type=str, required=True)
            p = parser.parse_args()
            ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
            db = get_session(DB_URL)
            # evt = db.query(EventRecord).filter_by(evt_id=evt_id).one()
            raw = ds.get(obs_id)
            obs = ObservationDAO(raw)
            obs.normalise()
            if is_true(p["bandpass"]):
                obs.bandpass(p["bandpassLow"], p["bandpassHigh"])
            if is_true(p["absolute"]):
                obs.absolute()
            paa = Paa(obs.series())
            paa_data = paa(p["paaInt"])
            paa_results = [{"x": int(k), "y": v} for k, v in json.loads(paa_data.to_json(orient="index")).items()]
            sax = Sax(paa_data)
            return {
                "original": obs.view(),
                "paa": paa_results,
                "sax": "".join([i for i in sax(p["alphabet"])])
            }
        except (PaaError, SaxError) as e:
            raise InternalServerError(e)
        except NoResultFound:
            raise NotFound
        except MultipleResultsFound:
            raise InternalServerError("Multiple results found, this is bad")
        except DatastoreError as e:
            raise InternalServerError(e)
