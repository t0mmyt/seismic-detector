from flask import jsonify, send_file
from flask_api import status
import re
from io import BytesIO
import requests
import logging


logger = logging.getLogger("interface")


file_from_cd = re.compile("filename=(.*)")


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
                error = jsonify({"error": "Got {} from {}".format(r.status_code, url)})
                logger.warning(error)
                return error, r.status_code
            elif r.status_code == status.HTTP_204_NO_CONTENT:
                return '', status.HTTP_204_NO_CONTENT
            if r.headers["Content-Type"] == "application/octet":
                cdh = r.headers["Content-Disposition"]
                m = file_from_cd.search(cdh)
                filename = m.group(1) if m else "untitled.SAC"
                data = BytesIO(r.content)
                data.seek(0)
                logger.debug("Got {} bytes from API".format(len(r.content)))
                return send_file(
                    data,
                    as_attachment=True,
                    attachment_filename=filename,
                    mimetype="application/octet"
                )
            data = r.json()
            return jsonify(data), status.HTTP_200_OK
        except requests.ConnectionError as e:
            return str(e), status.HTTP_503_SERVICE_UNAVAILABLE
        except (ValueError, TypeError) as e:
            logger.error(str(e))
            return str(e), status.HTTP_400_BAD_REQUEST
