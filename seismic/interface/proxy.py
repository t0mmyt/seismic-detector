from os import getenv
from flask_api import status
import requests


class ProxySax(object):
    def __init__(self, url=None):
        """
        Create a proxy to the SAX service

        Args:
            url: Optional URL to the SAX service
                 (if left out, SAX environment variable is used)
        """
        url = getenv('SAX', "http://localhost:8165") if not url else url
        self.url = "{}/v1/sax".format(url)

    def __call__(self, channel, **kwargs):
        """
        Send a request to the SAX service

        Args:
            channel:  Channel of observation
            **kwargs: Query parameters

        Returns:
            (content, status_code)
        """
        try:
            r = requests.get(
                url="{}/{}".format(self.url, channel),
                params=kwargs
            )
            data = r.json()
            return dict(data), status.HTTP_200_OK
        except requests.ConnectionError as e:
            return str(e), status.HTTP_503_SERVICE_UNAVAILABLE
        except (ValueError, TypeError) as e:
            return str(e), status.HTTP_400_BAD_REQUEST
