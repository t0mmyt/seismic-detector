#!/bin/sh

if [ ! $# -gt 0 ]; then echo "Need python app as argument" ; exit 101 ; fi

gunicorn --workers=4 --access-logfile=- -b 0.0.0.0:8000 --timeout=300 $@
