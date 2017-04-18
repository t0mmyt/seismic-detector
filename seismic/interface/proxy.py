from flask import request, jsonify
from flask_api import status
import requests


class Proxy(object):
    def __init__(self, url=None):
        """
        Create a proxy to the SAX service

        Args:
            url: Optional URL to the SAX service
                 (if left out, SAX environment variable is used)
        """
        self.url = url

    def __call__(self, path, **kwargs):
        """
        Send a request to the SAX service

        Args:
            channel:  Channel of observation
            **kwargs: Query parameters

        Returns:
            (content, status_code)
        """
        try:
            url = "{}/{}".format(self.url, path)
            r = requests.request(
                method=request.method,
                url=url,
                params=kwargs
            )
            if r.status_code > 400:
                return jsonify({"error": "Got {} from {}".format(r.status_code, url)}), r.status_code
            elif r.status_code == status.HTTP_204_NO_CONTENT:
                return '', status.HTTP_204_NO_CONTENT
            data = r.json()
            return jsonify(data), status.HTTP_200_OK
        except requests.ConnectionError as e:
            return str(e), status.HTTP_503_SERVICE_UNAVAILABLE
        except (ValueError, TypeError) as e:
            return str(e), status.HTTP_400_BAD_REQUEST
