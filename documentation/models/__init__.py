from flask_restplus import Model, fields

from documentation.models.login import *
from documentation.models.users import *
from documentation.models.parsers import *
from documentation.models.messages import *

authorizations = {
    'apiKey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

user_model = Model('user', {
    'username': fields.String,
    'password': fields.String,
    '_id': fields.String,
    'roles': fields.List(fields.String),
    'gallery': fields.List(fields.Nested(gallery_item)),
    'uploads': fields.List(fields.Nested(post_response)),
    'friends': fields.List(fields.Nested(friend_model)),
    'messages': fields.List(fields.Nested(message_model)),
    'email': fields.String
})