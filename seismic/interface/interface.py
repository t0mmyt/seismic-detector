"""
Main Web Interface
"""
import os
import requests
from collections import OrderedDict
from requests import ConnectionError
from flask import Flask, render_template, abort, request, jsonify
from flask_assets import assets, Environment, Bundle
from flask_api import status
from jinja2 import TemplateNotFound
from nav import SimpleNavigator
from importer import Importer
from proxy_sax import ProxySax


template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
app = Flask(__name__, template_folder=template_dir)
app.config['TEMPLATES_AUTO_RELOAD'] = True

env = Environment(app)

css = Bundle(
    "css/base.css",
    filters="cssmin",
    output="assets/css.min.css",
)
env.register("css_all", css)

nav = SimpleNavigator((
    ("Home", "/"),
    ("Import", "/import"),
    ("Explore/SAX", "/sax"),
))


@app.route("/")
def render_index():
    try:
        return render_template("index.html", nav=nav.render_as('Home'))
    except TemplateNotFound:
        abort(404)


@app.route("/import", methods=['GET', 'POST'])
def render_import():
    try:
        if request.method == "GET":
            return render_template("import.html", nav=nav.render_as('Import'))
        elif request.method == "POST":
            importer = Importer()
            files = request.files.getlist("files")
            for f in files:
                importer.add(f.read())
            status = importer.send()
            results = dict(zip([f.filename for f in files], status))
            results_html = "<table>"
            for filename, result in results.items():
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


@app.route("/sax")
def render_sax():
    try:
        return render_template("sax.html", nav=nav.render_as('Explore/SAX'))
    except TemplateNotFound:
        abort(404)


@app.route("/raw_json/<channel>")
def raw_json(channel):
    try:
        r = requests.get(
            "{}/v1/metrics/{}".format(TSDATASTORE, channel),
            params=request.args
        )
        if r.status_code != 200:
            abort(r.status_code)
        return jsonify(r.json())
    except ConnectionError:
        abort(503)


@app.route("/v1/sax/<channel>")
def proxy_sax(channel):
    proxy = ProxySax()
    response = proxy(channel, **request.args)
    # If we're 200, then return JSON, else as text
    if response[1] == status.HTTP_200_OK:
        return jsonify(response[0]), response[1]
    return response


if __name__ == "__main__":
    TSDATASTORE = os.getenv('TSDATASTORE', "http://localhost:8163")
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8000,
    )
