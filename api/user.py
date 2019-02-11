from resources import BaseResource
from resources.auth_resource import requires_auth
from accessors.user_accessor import UserAccessor
from documentation.namespaces import user_ns
from documentation.models import upload_parser, post_response, gallery_parser, paging_parser
from flask_restplus import fields
from helpers.file_transfers import encode_image_data
from helpers.image_server import ImageServer
from helpers import Environment
from requests_futures.sessions import FuturesSession
import json
from flask import request


session = FuturesSession()

message_model = user_ns.model('message', {
    'enlargement': fields.Integer(default=1),
    'tile_size': fields.Integer(default=8),
    'file_id': fields.String(default='example_id'),
})

pending_frame_model = user_ns.model('pending_frame', {
    'mimetype': fields.String,
    'filename': fields.String,
    'image_data': fields.String
})

pending_model_update = user_ns.model('pending_message', {
    'frame': fields.Nested(pending_frame_model, skip_none=True),
    'progress': fields.Float,
    'total_frames': fields.Integer,
})


@user_ns.route('/uploads')
class UserUploads(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @user_ns.doc(parser=upload_parser)
    def post(self, username):
        payload = upload_parser.parse_args()
        if 'file' not in payload:
            return {'message': 'A file is required!'}, 400
        upload_item = self.accessor.upload_file(username, payload['file'])
        return upload_item, 201

    @user_ns.doc(model=post_response)
    def get(self, username):
        return self.accessor.get_list(username, 'uploads')


@user_ns.route('/uploads/<string:file_id>')
class UserGalleryItem(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    def get(self, username, file_id):
        upload_item = self.accessor.get_upload_item(file_id, username=username)
        return upload_item

    def delete(self, username, file_id):
        self.accessor.delete_upload_item(file_id, username)
        return {'message': f'{file_id} deleted from  {username}'}


@user_ns.route('/messages')
class UserMessages(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @user_ns.expect(message_model)
    def post(self, username):
        try:
            url = f'{Environment().faas_url}/function/mosaic-maker'
            # url = 'http://localhost:8080/function/photomosaic-faas'
            # url = os.environ.get('PHOTOMOSAIC_URL', 'http://localhost:8080/function/photomosaic-faas')
            payload = user_ns.payload
            message = self.accessor.create_message_item(username, **payload)
            file_data = self.accessor.s3_accessor.get(payload.get('file_id'))
            body = {
                'file': encode_image_data(file_data.read()),
                'filename': file_data.filename,
                'username': username,
                'tile_size': payload.get('tile_size', 8),
                'enlargement': payload.get('enlargement', 1)
            }
            session.post(url, data=json.dumps(body))
            message['body'] = body
        except Exception as e:
            message = str(e)
        return message, 201

    def get(self, username):
        message_list = self.accessor.get_list(username, 'messages')
        return message_list


@user_ns.route('/pending')
class UserPending(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    def get(self, username):
        item = self.accessor.get_pending_frame(username)
        frame = item.get('frame')
        if frame:
            resp = ImageServer.serve_from_string(frame.get('image_data', ''), frame.get('mimetype', 'image/gif'))
        else:
            resp = ImageServer.serve_from_s3(item.get('file_id', ''))
        return resp


@user_ns.route('/pending_json')
class UserPendingJson(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @user_ns.expect(pending_model_update)
    def patch(self, username):
        payload = json.loads(request.data.decode('utf-8'))
        payload = payload if payload is not None else {}
        query = {'username': username}
        self.accessor.update_one(query, {
            '$set': {
                'messages.0.progress': payload.get('progress', 0),
                'messages.0.total_frames': payload.get('total_frames', 1)},
            '$push': {'messages.0.frames': {'$each': [payload.get('frame', {})], '$position': 0}}
        })
        return {'message': 'Success'}, 200

    def get(self, username):
        return self.accessor.get_pending_json(username)


@user_ns.route('/gallery')
class UserGallery(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @user_ns.expect(paging_parser)
    def get(self, username):
        args = paging_parser.parse_args()
        """Get all gallery items"""
        results = self.accessor.get_paginated_list(username, 'gallery', **args)
        self.page_builder.add_navigation(results, request.base_url, **args)
        return results

    @user_ns.expect(gallery_parser)
    def post(self, username):
        payload = gallery_parser.parse_args()
        mosaic_file = payload.get('mosaic_file')
        mosaic_data = mosaic_file.read()
        mosaic_filename = mosaic_file.filename
        alternate_file = payload.get('alternate_file')
        if alternate_file:
            alternate_data = alternate_file.read()
            alternate_filename = alternate_file.filename
        else:
            alternate_filename = None
            alternate_data = None
        result = self.accessor.create_gallery_item(username, image_data=mosaic_data, filename=mosaic_filename,
                                          gif_data=alternate_data, gif_filename=alternate_filename)
        return result


@user_ns.route('/gallery/<string:gallery_id>')
class UserGalleryItem(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    def get(self, username, gallery_id):
        gallery_item = self.accessor.get_gallery_item(gallery_id, username=username)
        return gallery_item

    def delete(self, username, gallery_id):
        self.accessor.delete_gallery_item(gallery_id, username)
        return {'message': f'{gallery_id} deleted from  {username}'}


@user_ns.route('/auth_gallery/<string:gallery_id>')
class UserGalleryItem(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @requires_auth(allowed_roles=['USER'])
    @user_ns.doc(security='apiKey')
    def get(self, username, gallery_id):
        gallery_item = self.accessor.get_gallery_item(gallery_id, username=username)
        return gallery_item

