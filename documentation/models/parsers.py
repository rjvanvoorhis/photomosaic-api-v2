__all__ = ['upload_parser', 'paging_parser', 'gallery_parser', 'pending_parser']

from flask_restplus import reqparse
from werkzeug.datastructures import FileStorage

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)

paging_parser = reqparse.RequestParser()
paging_parser.add_argument('skip', type=int)
paging_parser.add_argument('limit', type=int)


gallery_parser = reqparse.RequestParser()
gallery_parser.add_argument('mosaic_file', location='files', type=FileStorage, required=True)
gallery_parser.add_argument('alternate_file', location='files', type=FileStorage)


pending_parser = reqparse.RequestParser()
pending_parser.add_argument('frame', location='files', type=FileStorage, required=True)
pending_parser.add_argument('total_frames', type=int)
pending_parser.add_argument('progress', type=float)
