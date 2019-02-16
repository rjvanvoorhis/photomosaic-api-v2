__all__ = ['GridFsAccessor']

import logging
from pymongo import MongoClient
import gridfs
from helpers import Environment
from helpers.file_transfers import ImageStreamer
from werkzeug.utils import secure_filename
from uuid import uuid4


class GridFsAccessor(object):
    MONGODB_URI = Environment().mongodb_uri if Environment().mongodb_uri else 'mongodb://mongodb:27017/'

    def __init__(self, db=None, logger=None):
        db = db if db is not None else MongoClient(self.MONGODB_URI).photomosaic
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        self.db = db
        self.fs = gridfs.GridFS(self.db)
        self.streamer = ImageStreamer()

    def get(self, file_id):
        return self.fs.get(file_id)

    def put(self, data, **kwargs):
        file_id = self.fs.put(data, **kwargs)
        self.logger.debug(f'Saved file with file_id: {file_id}')
        return file_id

    def find_one(self, query=None, session=None, *args, **kwargs):
        item = self.fs.find_one(filter=query, session=session, *args, **kwargs)
        return item

    def delete(self, file_id):
        self.logger.debug(f'Removing file with file_id: {file_id}')
        self.fs.delete(file_id)

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
