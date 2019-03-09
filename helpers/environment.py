__all__ = ['Environment']
import os
from helpers.decorators import singleton


@singleton
class Environment(object):
    def __init__(self):
        self.default_env = {
            'email_server': 'smtp.googlemail.com',
            'mail_port': 465,
            'mail_use_tls': False,
            'mail_use_ssl': True,
            'cors_headers': 'Content-Type',
            'media_bucket': 'images',
            'mongodb_uri': 'mongodb://mongodb:27017/',
            'exclude_emails': [
                'photomosaic.api@gmail.com',
                'photomosaic.user.api@gmail.com',
                'photomosaic.admin.api@gmail.com'
            ]

        }

    def __getattr__(self, item):
        # environment variables overide default configuration
        env_var = {k.lower(): v for k, v in os.environ.items()}.get(item)
        return env_var if env_var is not None else self.default_env.get(item)
