from resources import BaseResource
from documentation.namespaces import user_ns
from documentation.models import upload_parser, post_response
from accessors import UserAccessor
from resources.auth_resource import requires_auth


@user_ns.doc(security='apiKey')
@user_ns.route('/uploads')
class UserUploads(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @requires_auth(allowed_roles='USER')
    @user_ns.doc(parser=upload_parser)
    def post(self, username):
        payload = upload_parser.parse_args()
        if 'file' not in payload:
            return {'message': 'A file is required!'}, 400
        upload_item = self.accessor.upload_file(username, payload['file'])
        return upload_item, 201

    @requires_auth(allowed_roles='USER')
    @user_ns.doc(model=post_response)
    def get(self, username):
        return self.accessor.get_list(username, 'uploads')


@user_ns.doc(security='apiKey')
@user_ns.route('/uploads/<string:file_id>')
class UserUploadItem(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @requires_auth(allowed_roles='USER')
    def get(self, username, file_id):
        upload_item = self.accessor.get_upload_item(file_id, username=username)
        return upload_item

    @requires_auth(allowed_roles='USER')
    def delete(self, username, file_id):
        self.accessor.delete_upload_item(file_id, username)
        return {'message': f'{file_id} deleted from  {username}'}
