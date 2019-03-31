__all__ = ['user_ns']
from flask_restplus import Namespace
from documentation.models import (login_model, registration_model, auth_model, message_model, gallery_item, metadata,
                                  friend_model, upload_img, user_model, comment_model, message_post, post_response,
                                  pending_frame_model, pending_model_update, add_role)

user_ns = Namespace('user', path='/users/<string:username>', description='User level operations')
for model in [login_model, registration_model, auth_model, metadata, message_model,
              friend_model, upload_img, user_model, gallery_item, comment_model, message_post, post_response,
              pending_frame_model, pending_model_update, add_role]:
    user_ns.add_model(model.name, model)