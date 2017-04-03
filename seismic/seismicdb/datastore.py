from minio import Minio, ResponseError
from io import BytesIO

class DatastoreError(Exception):
    pass


class Datastore(object):
    # TODO - Exceptions
    def __init__(self, endpoint, access_key, secret_key, bucket):
        try:
            self.m = Minio(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=False)
            self.bucket = bucket
            if not self.m.bucket_exists(bucket):
                self.m.make_bucket(bucket)
        except ResponseError as e:
            raise DatastoreError(e)

    def put(self, name, data, length):
        try:
            self.m.put_object(
                bucket_name=self.bucket,
                object_name=name,
                data=data,
                length=length
            )
        except ResponseError as e:
            raise DatastoreError(e)

    def get(self, name):
        try:
            return BytesIO(self.m.get_object(bucket_name=self.bucket, object_name=name).read())
        except ResponseError as e:
            raise DatastoreError(e)
