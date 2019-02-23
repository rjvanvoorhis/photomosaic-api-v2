__all__ = ['AuthorizationError', 'AuthResource', 'requires_auth']
from helpers import Environment, singleton
import jwt
import time
import logging
from accessors.user_accessor import UserAccessor
import functools
from flask import request
from jwt.exceptions import DecodeError


class AuthorizationError(Exception):
    pass


@singleton
class AuthResource(object):
    def __init__(self):
        self.logger = logging.getLogger()
        self.accessor = UserAccessor()
        self.secret = Environment().secret_key

    @staticmethod
    def bytes_to_bearer(token):
        return {'Authorization': f'Bearer {token.decode()}'}

    @staticmethod
    def bearer_to_bytes(header):
        header_str = header.get('Authorization', '')
        return header_str[7:].encode()

    def get_roles(self, username):
        return self.accessor.get_list(username, 'roles')

    def is_validated(self, username):
        return self.accessor.is_validated(username)

    def get_token(self, token):
        if isinstance(token, dict) and 'Authorization' in token:
            token = self.bearer_to_bytes(token)
        elif isinstance(token, str) and token.lower().startswith('bearer'):
            token = token[7:].encode()
        return jwt.decode(token, self.secret)

    def build_token(self, username):
        payload = {
            'username': username,
            'roles': self.get_roles(username),
            'validated': self.is_validated(username),
            'expire_at': time.time() + (60 * 60)
        }
        token = jwt.encode(payload, self.secret)
        return self.bytes_to_bearer(token)

    def verify_token(self, token, username, allowed_roles):
        allowed_roles = allowed_roles if allowed_roles else ['ADMIN']
        if isinstance(allowed_roles, str):
            allowed_roles = [allowed_roles]
        if 'ADMIN' not in allowed_roles:
            allowed_roles.append('ADMIN')  # ADMIN should always override
        try:
            payload = self.get_token(token)
            if (payload.get('expire_at') - time.time()) < 0:
                raise AuthorizationError('Token expired')
            elif not payload.get('validated', False):
                raise AuthorizationError('User has not been validated')
            elif 'ADMIN' in payload.get('roles', []):
                return {'message': 'Success'}, 200
            elif username != payload.get('username'):
                raise AuthorizationError('Username does not match')
            elif not any(role in allowed_roles for role in payload.get('roles', [])):
                raise AuthorizationError('User does not have the required roles')
        except (AuthorizationError, DecodeError) as e:
            return {'message': str(e)}, 403
        return {'message': 'Success'}, 200

    def check_password(self, username, password):
        status, msg = self.accessor.check_password(username, password)
        if not status:
            raise AuthorizationError(msg)
        return status

    def get_auth(self, username, password):
        if self.check_password(username, password):
            return self.build_token(username)

    def validate_user(self, username, password):
        if self.check_password(username, password):
            self.accessor.validate_user(username)
        return self.build_token(username)


def requires_auth(_func=None, *, allowed_roles=None):
    def decorator_requires_auth(func):
        @functools.wraps(func)
        def wrapper_requires_auth(*args, **kwargs):
            token = request.headers.get('Authorization')
            username = request.view_args.get('username')
            mesg, status = AuthResource().verify_token(token, username, allowed_roles)
            if status != 200:
                return mesg, status
            return func(*args, **kwargs)

        return wrapper_requires_auth

    if _func is None:
        return decorator_requires_auth
    else:
        return decorator_requires_auth(_func)
