from flask import jsonify
from flask_api import status
import requests
import logging


logger = logging.getLogger("interface")


class Proxy(object):
    def __init__(self, url=None):
        """
        Create a proxy to a service

        Args:
            url: Optional URL to the SAX service
                 (if left out, SAX environment variable is used)
        """
        self.url = url

    def __call__(self, path, orig_request):
        """
        Forward a request to the service defined at init

        Args:
            path (string): The path to communicate with on the API
            orig_request (flask.request): the original request object

        Returns:
            flask.response
        """
        try:
            url = "{}/{}".format(self.url, path)
            r = requests.request(
                url=url,
                method=orig_request.method,
                headers={key: value for (key, value) in orig_request.headers if key != 'Host'},
                params=orig_request.args,
                data=orig_request.get_data(),
            )
            if r.status_code >= 400:
                return jsonify({"error": "Got {} from {}".format(r.status_code, url)}), r.status_code
            elif r.status_code == status.HTTP_204_NO_CONTENT:
                return '', status.HTTP_204_NO_CONTENT
            data = r.json()
            return jsonify(data), status.HTTP_200_OK
        except requests.ConnectionError as e:
            return str(e), status.HTTP_503_SERVICE_UNAVAILABLE
        except (ValueError, TypeError) as e:
            return str(e), status.HTTP_400_BAD_REQUEST
