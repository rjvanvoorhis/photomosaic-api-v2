from flask_restplus import Api
from documentation.models import authorizations
from documentation.namespaces import base_ns
from documentation.namespaces import user_ns
from . import gallery, messages, signup, system, uploads


api = Api(title='Photomosaic API',
          description='A photomosaic API',
          prefix='/api/v1/photomosaic',
          authorizations=authorizations)

api.add_namespace(base_ns)
api.add_namespace(user_ns)
