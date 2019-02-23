from resources import BaseResource
from documentation.namespaces import user_ns
from accessors.user_accessor import UserAccessor
from resources.auth_resource import requires_auth


@user_ns.route('')
class UsersResource(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @requires_auth(allowed_roles='USER')
    def get(self, username):
        user = self.accessor.find_one({'username': username})
        return user

    @requires_auth(allowed_roles='USER')
    def delete(self, username):
        self.accessor.delete_user(username)
        return {'message': f'Deleted user: {username}'}
