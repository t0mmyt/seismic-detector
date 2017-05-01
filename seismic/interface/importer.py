from os import getenv
import logging
import requests
from flask_api import status


log = logging.getLogger("interface.import")


class Importer(object):
    def __init__(self, url=None):
        self.url = getenv('OBSERVATIONS', "http://localhost:8000") if not url else url
        self.status = {}

    def add(self, data, filename):
        try:
            r = requests.post(
                url=self.url + "/observations/",
                params={"filename": filename},
                headers={'Content-Type': "application/octet"},
                data=data
            )
            log.info("Got {} uploading {}".format(r.status_code, filename))
            self.status[filename] = (r.status_code == status.HTTP_201_CREATED)
        except requests.ConnectionError:
            return status.HTTP_503_SERVICE_UNAVAILABLE
