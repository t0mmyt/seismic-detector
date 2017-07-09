from flask_restplus import Api

from .observations import api as obs_ns
from .sax import api as sax_ns

api = Api(
    version="1.0",
    title="Seismic API",
    description="(Mostly) Restful API for operations on Seismic Data and SAX"
)

api.add_namespace(obs_ns)
api.add_namespace(sax_ns)
