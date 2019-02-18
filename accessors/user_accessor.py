__all__ = ['UserAccessor']

from accessors.mongo_db_accessor import MongoDbAccessor
from accessors.s3_accessor import S3Accessor
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from uuid import uuid4
import time
from helpers import Environment
DEFAULT_TIMEOUT = 1600


class UserException(Exception):
    pass


def set_password(password):
    psw_hash = generate_password_hash(password)
    return psw_hash


class UserAccessor(MongoDbAccessor):

    def __init__(self):
        super().__init__('users')
        self.s3_accessor = S3Accessor(logger=self.logger)
        self.env = Environment()

    def check_password(self, username, password):
        projection = {'_id': 0, 'username': 1, 'password_hash': 1, 'validated': 1}
        query = {'username': username}
        user = self.find_one(query, projection)
        if not user:
            status, msg = False, 'User not found'
        elif not user.get('password_hash'):
            status, msg = False, 'Password cannot be empty'
        else:
            status = check_password_hash(user['password_hash'], password)
            msg = 'Success' if status else 'Failure'
        return status, msg

    def is_validated(self, username):
        projection = {'_id': 0, 'validated': 1}
        return self.find_one({'username': username}, projection).get('validated', False)

    def get_paginated_list(self, username, field, skip=0, limit=None, sort=None):
        projection = {'_id': 0, field: 1}
        query = {'username': username}
        unwind = f'${field}'
        cursor = self.get_paginated_results(query, projection, unwind, skip, limit, sort)
        results = [item.get(field, {}) for item in cursor.get('results', [])]
        cursor['results'] = results
        return cursor

    def get_list(self, username, field):
        projection = {'_id': 0, field: 1}
        query = {'username': username}
        results = self.collection.find_one(query, projection)
        return results.get(field, [])

    def insert_list_item(self, username, field_name, item):
        query = {'username': username}
        to_update = {'$push': {
            field_name:
                {'$each': [item], '$position': 0}
        }}
        self.update_one(query, to_update)

    def create_message_item(self, username, file_id, enlargement=1, tile_size=1):
        message = {
            'file_id': file_id,
            'enlargement': enlargement,
            'tile_size': tile_size,
            'current': file_id,
            'progress': 0,
            'message_id': str(uuid4()),
            'status': 'queued',
            'expire_at': time.time() + DEFAULT_TIMEOUT,
            'total_frames': 50,
            'frames': []
        }
        self.insert_list_item(username, 'messages', message)
        return message

    def create_gallery_item(self, username, image_data, filename, gif_data=None, gif_filename=None):
        img_id, thumbnail_id = self.s3_accessor.insert_image_and_thumbnail(image_data, filename=filename)
        if not gif_data:
            alternate_id, thumbnail_alternate_id = (img_id, thumbnail_id)
        else:
            gif_filename = secure_filename(f'{str(uuid4())}.gif') if gif_filename is None else gif_filename
            alternate_id, thumbnail_alternate_id = self.s3_accessor.insert_image_and_thumbnail(
                gif_data, filename=gif_filename)
        gallery_item = {
            'username': username,
            'gallery_id': str(uuid4()),
            'file_ids': [img_id, thumbnail_id, alternate_id, thumbnail_alternate_id],
            'mosaic_url': f'{self.env.s3_external_url}/images/{img_id}',
            'alternate_url': f'{self.env.s3_external_url}/images/{alternate_id}',
            'thumbnail_url': f'{self.env.s3_external_url}/images/{thumbnail_id}',
            'alternate_thumbnail_url': f'{self.env.s3_external_url}/images/{thumbnail_alternate_id}',
            'toggle_on': True,
        }
        self.insert_list_item(username, 'gallery', gallery_item)
        self.complete_job(username)
        return gallery_item

    def upload_file(self, username, img_file):
        path = secure_filename(f'{uuid4()}_{img_file.filename}')
        img_data = img_file.read()
        img_id, thumbnail_id = self.s3_accessor.insert_image_and_thumbnail(img_data, filename=path)
        upload_object = {
            'img_path': path,
            'file_id': img_id,
            'thumbnail_id': thumbnail_id
        }
        self.insert_list_item(username, 'uploads', upload_object)
        return upload_object

    def create_user(self, username, email, password):
        user = {
            'password_hash': set_password(password),
            'username': username,
            'email': email,
            'validated': False,
            'gallery': [],
            'uploads': [],
            'messages': [],
            'friends': [],
            'roles': ['USER'],
            '_id': str(uuid4())
        }
        query = {'$or': [{'email': user['email']}, {'username': user['username']}]}
        if self.collection.count(query):
            raise UserException(f'Error: username {username} or email {email} are already associated with an account')
        self.collection.insert_one(user)
        return user

    def get_pending_json(self, username):
        pipeline = [
            {'$match': {'username': username}},
            {'$project': {'message': {'$arrayElemAt': ['$messages', 0]}}},
            {'$project': {
                'message.file_id': 1,
                '_id': 0,
                'message.message_id': 1,
                'message.progress': 1,
                'message.expire_at': 1,
                # 'message.frame': {'$arrayElemAt': ['$message.frames', 0]}
            }}
        ]
        message = self.aggregate(pipeline)
        message = message[0] if message else {}
        return message.get('message', {})

    def get_pending_frame(self, username):
        pipeline = [
            {'$match': {'username': username}},
            {'$project': {'message': {'$arrayElemAt': ['$messages', 0]}}},
            {'$project': {
                'message.file_id': 1,
                '_id': 0,
                # 'message.message_id': 1,
                # 'message.progress': 1,
                # 'message.expire_at': 1,
                'message.frame': {'$arrayElemAt': ['$message.frames', 0]}
            }}
        ]
        message = self.aggregate(pipeline)
        message = message[0] if message else {}
        return message.get('message', {})

    def complete_job(self, username):
        query = {'username': username}
        self.update_one(
            query,
            {'$set': {
                'messages.0.progress': 1.0,
                'messages.0.status': 'complete'},
             '$push': {'messages.0.frames': {'$each': [], '$slice': -1}}}
        )

    def validate_user(self, username):
        query = {'username': username}
        self.update_one(query, {'$set': {'validated': True}})

    def get_gallery_item(self, gallery_id, username=None):
        query = {'username': username} if username is not None else {}
        sub_query = {'gallery.gallery_id': gallery_id}
        gallery_item = self.get_array_element(query, 'gallery', sub_query)
        return gallery_item

    def get_upload_item(self, file_id, username=None):
        query = {'username': username} if username is not None else {}
        sub_query = {'uploads.file_id': file_id}
        gallery_item = self.get_array_element(query, 'uploads', sub_query)
        return gallery_item

    def delete_gallery_item(self, gallery_id, username=None):
        query = {'username': username} if username is not None else {}
        gallery_item = self.get_gallery_item(gallery_id, username)
        if gallery_item:
            for file_id in list(set(gallery_item.get('file_ids', []))):
                self.s3_accessor.delete_object(file_id, self.env.media_bucket)
        self.delete_one_element(query, 'gallery', {'gallery_id': gallery_id})

    def delete_upload_item(self, file_id, username=None):
        query = {'username': username} if username is not None else {}
        upload_item = self.get_upload_item(file_id, username)
        if upload_item:
            for _id in [upload_item.get(k, '') for k in ['file_id', 'thumbnail_id']]:
                self.s3_accessor.delete_object(_id, self.env.media_bucket)
        self.delete_one_element(query, 'uploads', {'file_id': file_id})

    def delete_user(self, username):
        user = self.find_one({'username': username})
        for gallery_item in user.get('gallery'):
            for file_id in list(set(gallery_item.get('file_ids', []))):
                self.s3_accessor.delete_object(file_id, self.env.media_bucket)
        for upload_item in user.get('uploads'):
            for _id in [upload_item.get(k, '') for k in ['file_id', 'thumbnail_id']]:
                self.s3_accessor.delete_object(_id, self.env.media_bucket)
        self.collection.delete_one({'username': username})
