__all__ = ['S3Accessor']

import logging
import boto3
from helpers import Environment, singleton
from uuid import uuid4
from helpers.file_transfers import ImageStreamer
from werkzeug.utils import secure_filename


@singleton
class S3Accessor(object):

    def __init__(self, logger=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.env = Environment()
        self.streamer = ImageStreamer()
        self.client = boto3.client(
            's3',
            endpoint_url=self.env.s3_endpoint_url,
            aws_access_key_id=self.env.aws_access_key_id,
            aws_secret_access_key=self.env.aws_secret_access_key
        )
        self.resource = boto3.resource(
            's3',
            endpoint_url=self.env.s3_endpoint_url,
            aws_access_key_id=self.env.aws_access_key_id,
            aws_secret_access_key=self.env.aws_secret_access_key
        )

    def create_bucket(self, bucket_name, acl='public-read'):
        return self.client.create_bucket(Bucket=bucket_name, ACL=acl)

    def put(self, data, bucket_name=None, _id=None, mimetype=None, filename=None):
        mimetype = mimetype if mimetype else 'application/octet-stream'
        file_id = _id if _id else str(uuid4())
        bucket_name = bucket_name if bucket_name else self.env.media_bucket
        self.client.put_object(Body=data, Key=file_id, Bucket=bucket_name, ContentType=mimetype,
                               Metadata={'mimetype': mimetype, 'filename': filename})
        return file_id

    def get(self, file_id, bucket_name=None):
        bucket_name = bucket_name if bucket_name else self.env.media_bucket
        resp = self.client.get_object(Key=file_id, Bucket=bucket_name)
        metadata = resp.get('Metadata', {})
        body = resp['Body']
        body.filename = metadata.get('filename')
        body.mimetype = metadata.get('mimetype')
        return body

    def insert_image_and_thumbnail(self, image_data, filename=None):
        img_id = str(uuid4())
        file_id = str(uuid4())
        data = self.streamer.load(image_data).dump()
        filename = filename if filename is not None else data.get('filename')
        filename = secure_filename(filename)
        mimetype = data.get('mimetype')
        thumbnail_filename = f'thumbnail_{filename}'
        img_id = self.put(data.get('image'), _id=img_id, filename=filename, mimetype=mimetype)
        thumbnail_id = self.put(data.get('thumbnail'), _id=file_id, filename=thumbnail_filename, mimetype=mimetype)
        return img_id, thumbnail_id

    def delete_object(self, file_id, bucket_name=None):
        bucket_name = bucket_name if bucket_name else self.env.media_bucket
        self.resource.Object(bucket_name, file_id).delete()

    def delete_bucket(self, bucket_name):
        bucket = self.resource.Bucket(bucket_name)
        bucket.objects.all().delete()
        bucket.delete()

    def health(self):
        is_alive = False
        try:
            self.client.head_bucket(Bucket=self.env.media_bucket)
            is_alive = True
        except Exception as e:
            self.logger.exception(e)
        return is_alive
