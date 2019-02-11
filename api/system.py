import requests
from accessors import UserAccessor, S3Accessor
from resources import BaseResource
from helpers import Environment
from helpers.image_server import ImageServer
from documentation.namespaces import base_ns


@base_ns.route('/system/version')
class Version(BaseResource):
    def get(self):
        self.logger.debug('Fetching version resource')
        return {'service': 'PHOTOMOSAIC API', 'version': '0.0.0'}, 200


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


@base_ns.route('/images/<string:file_id>')
class Images(BaseResource):
    def __init__(self, api=None):
        super().__init__(api=api)
        self.image_server = ImageServer()

    @base_ns.produces(['image/*'])
    def get(self, file_id):
        return self.image_server.serve_from_s3(file_id)
