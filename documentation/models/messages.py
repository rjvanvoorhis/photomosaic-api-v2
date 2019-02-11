__all__ = ['message_model', 'pending_model_update', 'pending_frame_model']
from flask_restplus import fields, Model


message_model = Model('message', {
    'enlargement': fields.Integer(default=1),
    'tile_size': fields.Integer(default=8),
    'file_id': fields.String(default='example_id'),
})

pending_frame_model = Model('pending_frame', {
    'mimetype': fields.String,
    'filename': fields.String,
    'image_data': fields.String
})

pending_model_update = Model('pending_message', {
    'frame': fields.Nested(pending_frame_model, skip_none=True),
    'progress': fields.Float,
    'total_frames': fields.Integer,
})