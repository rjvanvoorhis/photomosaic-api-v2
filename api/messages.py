import json
from flask import request
from requests_futures.sessions import FuturesSession
from resources import BaseResource
from helpers import Environment
from accessors import UserAccessor, GridFsAccessor
from helpers.file_transfers import encode_image_data
from helpers.image_server import ImageServer

from documentation.namespaces import user_ns
from documentation.models import message_model, pending_model_update
from documentation.models import pending_parser
from resources.auth_resource import requires_auth

session = FuturesSession()


@user_ns.doc(security='apiKey')
@user_ns.route('/messages')
class UserMessages(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @requires_auth(allowed_roles='USER')
    @user_ns.expect(message_model)
    def post(self, username):
        auth_token = request.headers.get('Authorization')
        try:
            url = f'{Environment().faas_url}/function/mosaic-maker'
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
            headers = {
                'Authorization': auth_token,
                'Content-Type': 'application/json',
                'X-MOSAIC_API_URL': Environment().mosaic_api_url_internal
            }
            session.post(url, data=json.dumps(body), headers=headers)
            message['body'] = body
        except Exception as e:
            message = str(e)
        return message, 201

    @requires_auth(allowed_roles='USER')
    def get(self, username):
        message_list = self.accessor.get_list(username, 'messages')
        return message_list


# @user_ns.doc(security='apiKey')
@user_ns.route('/pending')
class UserPending(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    # @requires_auth(allowed_roles='USER')
    def get(self, username):
        item = self.accessor.get_pending_frame(username)
        frame = item.get('frame')
        if frame:
            resp = ImageServer.serve_from_mongodb(frame)
            # resp = ImageServer.serve_from_string(frame.get('image_data', ''), frame.get('mimetype', 'image/gif'))
        else:
            resp = ImageServer.serve_from_s3(item.get('file_id', ''))
        return resp


@user_ns.doc(security='apiKey')
@user_ns.route('/pending_json')
class UserPendingJson(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()
        self.grid_fs_accessor = GridFsAccessor(db=self.accessor.db)

    @user_ns.expect(pending_parser)
    def patch(self, username):
        payload = pending_parser.parse_args()
        if 'frame' not in payload:
            return {'Message': 'Failure, a file is required'}, 400
        frame = payload.get('frame')
        frame_id = self.grid_fs_accessor.put(frame, mimetype=frame.content_type)

        # payload = json.loads(request.data.decode('utf-8'))
        # payload = payload if payload is not None else {}
        query = {'username': username}
        self.accessor.update_one(query, {
            '$set': {
                'messages.0.progress': payload.get('progress', 0),
                'messages.0.total_frames': payload.get('total_frames', 1)},
            '$push': {'messages.0.frames': {'$each': [frame_id], '$position': 0}}
        })
        return {'message': 'Success'}, 200

    @requires_auth(allowed_roles='USER')
    def get(self, username):
        return self.accessor.get_pending_json(username)
