from os import getenv
from celery import Celery

from seismic.datastore import Datastore, DatastoreError

MINIO_HOST = getenv("MINIO_HOST", "localhost:9000")
MINIO_ACCESS_KEY = getenv("MINIO_ACCESS_KEY", "dev-TKE8KC10YL")
MINIO_SECRET_KEY = getenv("MINIO_SECRET_KEY", "dev-ALUP1N7WUO")
MINIO_BUCKET = getenv("MINIO_BUCKET", "raw")
DB_URL = "postgresql://seismic:d3v3l0pm3nt!@localhost:5432/seismic"
BROKER_URL = getenv("BROKER_URL", "redis://localhost:6379")

app = Celery('tasks', broker=BROKER_URL)


@app.task()
def datastore_read(obs_id):
    ds = Datastore(MINIO_HOST, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET)
    data = ds.get(obs_id)
    return data.getbuffer().nbytes

