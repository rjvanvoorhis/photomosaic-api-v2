from flask import make_response
from helpers.file_transfers import ImageStreamer
from accessors.grid_fs_accessor import GridFsAccessor
from accessors.s3_accessor import S3Accessor
from helpers import Environment
from helpers.file_transfers import decode_image_data


class ImageServer(object):
    def __init__(self):
        self.streamer = ImageStreamer()

    @staticmethod
    def serve_from_mongodb(file_id):
        img = GridFsAccessor().get(file_id)
        resp = make_response(img.read())
        resp.content_type = img.mimetype
        return resp

    @staticmethod
    def serve_from_s3(file_id, bucket_name=None):
        try:
            bucket_name = bucket_name if bucket_name else Environment().media_bucket
            img = S3Accessor().get(file_id, bucket_name=bucket_name)
            resp = make_response(img.read())
            resp.content_type = img.mimetype
        except Exception as ex:
            resp = str(ex)
        return resp

    @staticmethod
    def serve_from_string(image_string, mimetype='image/gif'):
        image_data = decode_image_data(image_string)
        resp = make_response(image_data)
        resp.content_type = mimetype
        return resp

