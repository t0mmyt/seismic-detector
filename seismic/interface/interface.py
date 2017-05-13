"""
Main Web Interface
"""
import os
from os import getenv
from flask import Flask, render_template, abort, request, send_from_directory, jsonify
from flask_api import status
from jinja2 import TemplateNotFound
from celery import Celery, chain
import logging

from seismic.interface.nav import SimpleNavigator
from seismic.interface.importer import Importer
from seismic.interface.proxy import Proxy
from seismic.interface.errors import ErrorHandler
from seismic.worker.tasks import detector, make_graphs

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
app = Flask("interface", template_folder=template_dir)
app.config['TEMPLATES_AUTO_RELOAD'] = True

nav = SimpleNavigator((
    ("Home", "/"),
    ("Import", "/import"),
    ("Observations", "/observations"),
    ("Explore/SAX", "/sax"),
    ("Tasks", "/tasks"),
))


OBSERVATIONS = getenv("OBSERVATIONS", "http://localhost:8000")
SAX = getenv("SAX", "http://localhost:8001")
BROKER_URL = getenv("BROKER_URL", "redis://localhost:6379")
celery_app = Celery('tasks', broker=BROKER_URL)


@app.errorhandler(ErrorHandler)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def send_relative_dir(d, f):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), d)
    return send_from_directory(d, f)


# TODO - Favicon
@app.route("/favicon.ico")
def favicon():
    return send_relative_dir("assets", "favicon.ico")


# Assets
@app.route("/assets/<path:path>", )
def static_css(path):
    return send_relative_dir("assets/", path)


@app.route("/")
def page_index():
    try:
        return render_template("index.html", nav=nav.render_as('Home'))
    except TemplateNotFound:
        abort(404)


@app.route("/import", methods=['GET', 'POST'])
def page_import():
    try:
        if request.method == "GET":
            return render_template("import.html", nav=nav.render_as('Import'))
        elif request.method == "POST":
            importer = Importer()
            files = request.files.getlist("files")
            for f in files:
                importer.add(f.read(), filename=f.filename)
            results_html = "<table>"
            for filename, result in importer.status.items():
                if result:
                    results_html += '<tr class="success"><td>{}</td></tr>'.format(filename)
                else:
                    results_html += '<tr class="failure"><td>{}</td></tr>'.format(filename)
            results_html += "</table>"

            return render_template(
                "import.html",
                nav=nav.render_as("Import"),
                results=results_html,
            )
    except TemplateNotFound:
        abort(404)


@app.route("/<page>")
def page_generic(page):
    """
    Renders a page that has a template, needs no further processing from the 
    interface module and the Navigation element can be inferred from the page 
    name. (e.g observations: template=observations.html, title='Observations')

    Args:
        page: page to render
    """
    try:
        return render_template(
            "{}.html".format(page),
            nav=nav.render_as(page.title())
        )
    except TemplateNotFound:
        abort(status.HTTP_404_NOT_FOUND)


@app.route("/observations/<path:path>", methods=["GET", "DELETE"])
def view_observations(path):
    """
    Proxy requests with /observation prefix to the Observations API
    
    Args:
        path: relative path on query service

    Returns:
        JSON
    """
    proxy = Proxy(OBSERVATIONS)
    return proxy("observations/{}".format(path), **request.args.to_dict())


@app.route("/sax/<path:path>", methods=["GET", "DELETE"])
def view_sax(path):
    """
    Proxy requests with /sax prefix to the SAX API

    Args:
        path: relative path on query service

    Returns:
        JSON
    """
    proxy = Proxy(SAX)
    app.logger.debug("Sending to SAX")
    return proxy("sax/{}".format(path), **request.args.to_dict())


@app.route("/sax")
def page_sax():
    try:
        return render_template("explore.html", nav=nav.render_as('Explore/SAX'))
    except TemplateNotFound:
        abort(404)


@app.route("/run/<task_name>")
def run_task(task_name):
    if task_name == "detect":
        req_params = ("obsId", "bandpassLow", "bandpassHigh", "shortWindow", "longWindow", "nStds", "triggerLen")
        missing_params = [k for k in req_params if k not in request.args]
        if len(missing_params) > 0:
            raise ErrorHandler("Missing parameters: {}".format(", ".join(missing_params)))
        # TODO - This does not support multiple traces in a file (see Eww)
        task = chain(
            detector.s(
                obs_id=request.args['obsId'],
                trace=0,  # <- Eww
                bp_low=int(request.args['bandpassLow']),
                bp_high=int(request.args['bandpassHigh']),
                short_window=int(request.args['shortWindow']),
                long_window=int(request.args['longWindow']),
                nstds=int(request.args['nStds']),
                trigger_len=int(request.args['triggerLen']),
            ),
            # make_graphs.s()
        ).apply_async()
        return jsonify({"taskId": task.id})
    else:
        abort(404)

if __name__ == "__main__":
    TSDATASTORE = os.getenv('TSDATASTORE', "http://localhost:8163")
    # app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(logging.DEBUG)
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080,
    )
