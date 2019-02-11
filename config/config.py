__all__ = ['EMAIL_SERVER', 'MAIL_PASSWORD', 'MAIL_USE_TLS', 'ADMINS',
           'MAIL_PORT', 'MAIL_USE_SSL', 'MAIL_USERNAME']

from helpers import Environment
env = Environment()

EMAIL_SERVER = 'smtp.googlemail.com'
MAIL_USERNAME = env.mail_username
MAIL_PASSWORD = env.mail_password
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
CORS_HEADERS = 'Content-Type'

ADMINS = ['photomosaic.api@gmail.com']
