from os import getenv
import requests
from flask_api import status


class Importer(object):
    def __init__(self, url=None):
        url = getenv('OBSLOADER', "http://localhost:8164") if not url else url
        self.url = "{}/v1/observations".format(url)
        self.data = []

    def add(self, data):
        self.data.append(data)

    def send(self):
        status = []
        for data in self.data:
            status.append(self._upload(data) == 204)
        return status

    def _upload(self, data):
        try:
            r = requests.put(
                url=self.url,
                headers={'Content-Type': "application/octet"},
                data=data
            )
            return r.status_code
        except requests.ConnectionError:
            return status.HTTP_503_SERVICE_UNAVAILABLE
