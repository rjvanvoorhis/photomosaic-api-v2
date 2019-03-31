from resources import BaseResource
from documentation.namespaces import user_ns
from accessors.user_accessor import UserAccessor
from resources.auth_resource import requires_auth, AuthResource
from helpers import Environment
from flask import request
from documentation.models import add_role


@user_ns.doc(security='apiKey')
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


@user_ns.doc(security='apiKey')
@user_ns.route('/role')
class UserRolesResource(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = AuthResource()

    @user_ns.expect(add_role)
    def patch(self, username):
        if Environment().environment != 'test':
            token = request.headers.get('Authorization')
            msg, status = self.accessor.verify_token(token, username, ['ADMIN'])
            if status != 200:
                return msg, status
        role = user_ns.payload.get('role', 'USER')
        self.accessor.add_role(username, role)
        return {'message': f'Added {role} role to {username}'}, 200
