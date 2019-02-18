import base64
import time
import json

from resources import BaseResource, AuthResource, AuthorizationError
from accessors import UserAccessor, MailAccessor
from helpers import Environment
from documentation.namespaces import base_ns
from documentation.models import login_model, registration_model


@base_ns.route('/validate')
class ValidateUser(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.resource = AuthResource()

    @base_ns.expect(login_model)
    def post(self):
        payload = base_ns.payload
        try:
            header = self.resource.validate_user(**payload)
        except AuthorizationError as e:
            self.logger.exception(str(e))
            return {'message': str(e)}, 401
        return header


@base_ns.route('/login')
class Login(BaseResource):

    def __init__(self, api=None):
        super().__init__(api=api)
        self.resource = AuthResource()

    @base_ns.expect(login_model)
    def post(self):
        payload = base_ns.payload
        try:
            header = self.resource.get_auth(**payload)
        except AuthorizationError as e:
            self.logger.exception(str(e))
            return {'message': str(e)}, 401
        return header


@base_ns.route('/register')
class Registration(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.accessor = UserAccessor()

    @base_ns.expect(registration_model)
    def post(self):
        payload = base_ns.payload
        try:
            user = self.accessor.create_user(**payload)
            mail = MailAccessor()
            info = {'username': user.get('username'), 'expireAt': (time.time() + 10800) * 1000}
            token = str(base64.b64encode(json.dumps(info).encode()))[2:-1]
            html = f'''
            <b>HELLO {user.get("username")}!</b>
            <p>Follow this link to verify your account</p>
            <p>The link will expire in 3 hours</p>
            <a href="{Environment().front_end_url}/validate?token={token}">Validate</a>
            '''
            mail.send_mail(user.get('email'), html, subject='New Photomosaic User')
            mail.quit()
        except Exception as e:
            self.logger.exception(str(e))
            return {'message': str(e)}, 401
        return {'message': 'sent email'}, 200
