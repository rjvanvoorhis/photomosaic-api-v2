__all__ = ['login_model', 'registration_model', 'auth_model']
from flask_restplus import Model, fields


login_model = Model('login_model', {
    'username': fields.String,
    'password': fields.String
})

registration_model = login_model.clone('registration_model', {
    'email': fields.String
})

auth_model = Model('auth_model', {
    'Authorization': fields.String(example='Bearer token')
})
