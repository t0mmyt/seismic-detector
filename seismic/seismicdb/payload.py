import numpy as np
from io import BytesIO
from logging import debug
import bz2


class PayloadError(Exception):
    pass


class Payload(object):
    def to_np_save(self):
        b = BytesIO()
        np.save(b, self.datapoints)
        b.seek(0)
        c = bz2.compress(b.read())
        return len(c), BytesIO(c)


class PayloadFromImport(Payload):
    def __init__(self, data):
        if isinstance(data, dict):
            for i in ('tags', 'start', 'interval', 'datapoints'):
                if i not in data:
                    raise PayloadError("{} was not found in payload.".format(i))
            if not isinstance(data['datapoints'], list):
                raise PayloadError("Datapoints should be a list")
            data['datapoints'] = np.array(data['datapoints'])
            self.__dict__.update(data)
        else:
            raise PayloadError("Payload was not a dict object")


class PayloadFromObject(object):
    def __init__(self, data, meta):
        if isinstance(data, BytesIO):
            try:
                raw = BytesIO(bz2.decompress(data.read()))
                self.datapoints = np.load(raw)
            except (TypeError, OSError) as e:
                raise PayloadError("Could not decompress: {}".format(e))
            self.__dict__.update(meta)
        else:
            raise PayloadError("Data was not a BytesIO object (got: {})".format(type(data)))
