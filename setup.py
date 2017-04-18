# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='seismic',
    version='1.0',
    author='Tom Taylor',
    author_email='tom+seismic@tomm.yt',
    url='https://github.com/t0mmyt/seismic-detector',
    description='Seismic event detection and analysis',
    packages=find_packages(),
    include_package_data=True,
    scripts=(
        "run_gunicorn.sh",
    ),
    install_requires=(
        'numpy',
        'scipy',
        'matplotlib',
        'obspy',
        'iso8601',
        'pandas',
        'pytz',
        'sqlalchemy',
        'psycopg2',
        'minio',
        'msgpack-python',
        'gunicorn',
        'flask',
        'flask-appconfig>=0.10',
        'flask-api',
        'requests',
        'celery',
        'redis',
        'flask-api',
    )
)
