__all__ = ['base_ns']
from flask_restplus import Namespace
from documentation.models import (login_model, registration_model, auth_model, message_model, gallery_item, metadata,
                                  friend_model, upload_img, user_model)

base_ns = Namespace('base', path='/', description='Base level operations')
for model in [login_model, registration_model, auth_model, metadata, message_model,
              friend_model, upload_img, user_model, gallery_item]:
    base_ns.add_model(model.name, model)
