import json
from flask import request
from requests_futures.sessions import FuturesSession
from resources import BaseResource
from helpers import Environment
from accessors import UserAccessor
from helpers.file_transfers import encode_image_data
from helpers.image_server import ImageServer

from documentation.namespaces import user_ns
from documentation.models import message_model, pending_model_update

session = FuturesSession()


@user_ns.route('/messages')
class UserMessages(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @user_ns.expect(message_model)
    def post(self, username):
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
