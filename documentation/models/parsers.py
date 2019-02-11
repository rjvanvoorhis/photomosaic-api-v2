__all__ = ['upload_parser', 'paging_parser', 'gallery_parser']

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