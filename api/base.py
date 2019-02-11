import requests
import time
import base64
import json
from accessors.user_accessor import UserAccessor, S3Accessor
from resources import BaseResource, AuthorizationError, AuthResource
from helpers.image_server import ImageServer
from helpers import Environment
from documentation.namespaces.base import base_ns, registration_model, login_model
from accessors.mail_accessor import MailAccessor


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


@base_ns.route('/system/version')
class Version(BaseResource):
    def get(self):
        return {'service': 'PHOTOMOSAIC API','version': '0.0.0'}, 200


@base_ns.route('/system/health_check')
class HealthCheck(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.env = Environment()

    def get(self):
        def health_string(val):
            return 'SUCCESS' if val else 'FAILURE'
        health_check = {
            'photomosaic_api': health_string(self.faas_health()),
            's3_connection': health_string(S3Accessor().health()),
            'mongo_connection': health_string(UserAccessor().health())
        }
        code = 500 if 'FAILURE' in health_check.values() else 200
        return health_check, code

    def faas_health(self):
        url = f'{self.env.faas_url}/function/mosaic-healthcheck'
        try:
            requests.get(url)
            code = 200
        except Exception as e:
            self.logger.exception(str(e))
            code = 500
        return code == 200


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


@base_ns.route('/images/<string:file_id>')
class Images(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.image_server = ImageServer()

    @base_ns.produces(['image/*'])
    def get(self, file_id):
        return self.image_server.serve_from_s3(file_id)

