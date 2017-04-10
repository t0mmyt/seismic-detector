"""
Main Web Interface
"""
import os
from os import getenv
from flask import Flask, render_template, abort, request, jsonify, send_from_directory
from jinja2 import TemplateNotFound

from seismic.interface.nav import SimpleNavigator
from seismic.interface.importer import Importer
from seismic.interface.proxy import Proxy

template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
app = Flask(__name__, template_folder=template_dir)
app.config['TEMPLATES_AUTO_RELOAD'] = True

nav = SimpleNavigator((
    ("Home", "/"),
    ("Import", "/import"),
    ("Observations", "/observations"),
    ("Explore/SAX", "/sax"),
))

QUERY = getenv("QUERY", "http://localhost:8003")


# CSS Assets
@app.route("/css/<path:path>", )
def static_css(path):
    return send_from_directory("assets/css", path)


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


@app.route("/observations")
def page_observations():
    return render_template(
        "observations.html",
        nav=nav.render_as("Observations")
    )


@app.route("/observations/<path>")
def ajax_observations(path):
    proxy = Proxy(QUERY)
    return proxy(path, **request.args.to_dict())


@app.route("/sax")
def page_sax():
    try:
        return render_template("sax.html", nav=nav.render_as('Explore/SAX'))
    except TemplateNotFound:
        abort(404)





# @app.route("/raw_json/<channel>")
# def raw_json(channel):
#     try:
#         r = requests.get(
#             "{}/v1/metrics/{}".format(TSDATASTORE, channel),
#             params=request.args
#         )
#         if r.status_code != 200:
#             abort(r.status_code)
#         return jsonify(r.json())
#     except ConnectionError:
#         abort(503)
#
#
# @app.route("/v1/sax/<channel>")
# def proxy_sax(channel):
#     proxy = ProxySax()
#     response = proxy(channel, **request.args)
#     # If we're 200, then return JSON, else as text
#     if response[1] == status.HTTP_200_OK:
#         return jsonify(response[0]), response[1]
#     return response


if __name__ == "__main__":
    TSDATASTORE = os.getenv('TSDATASTORE', "http://localhost:8163")
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080,
    )
