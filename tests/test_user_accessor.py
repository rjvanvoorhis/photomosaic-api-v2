import unittest
from tests.utilities import BaseTest
from accessors import user_accessor
from ddt import ddt, data, unpack
from mock import patch, MagicMock
import time


@ddt
class UserAccessorTest(BaseTest):
    import_route = 'accessors.user_accessor'

    def setUp(self):
        self.s3_accessor = self.add_patcher('S3Accessor')
        self.logger = self.add_patcher('logging', 'accessors.mongo_db_accessor').getLogger.return_value
        self.mock_client = self.add_patcher('MongoClient', 'accessors.mongo_db_accessor')
        self.mock_env = self.add_patcher('Environment').return_value
        self.mock_env.mongodb_uri = 'mock_uri'
        self.mock_env.media_bucket = 'media_bucket'
        self.mock_paginator = self.add_patcher('Paginator', 'accessors.mongo_db_accessor')
        self.add_freeze('2012-04-14 10:00:01')
        self.mock_id = self.add_patcher('uuid4')

    def get_collection(self):
        return self.mock_client.return_value.photomosaic.__getitem__.return_value

    def test_init(self):
        accessor = user_accessor.UserAccessor()
        # from pdb import set_trace as bp
        self.assertEqual(accessor.collection_name, 'users')
        self.s3_accessor.assert_called_with(logger=self.logger)

    @data(
        ({'password_hash': user_accessor.set_password('real_pswd')}, 'real_pswd', (True, 'Success')),
        ({'password_hash': user_accessor.set_password('real_pswd')}, 'bad_pswd', (False, 'Failure')),
        ({}, 'real_pswd', (False, 'User not found')),
        ({'username': 'username'}, 'real_pswd', (False, 'Password cannot be empty')),
    )
    @unpack
    @patch.object(user_accessor.UserAccessor, 'find_one')
    def test_check_password(self, user, pswd, result, mock_find):
        mock_find.return_value = user
        accessor = user_accessor.UserAccessor()
        res = accessor.check_password('username', pswd)
        self.assertEqual(res, result)

    @data(
        ({}, False),
        ({'validated': True}, True),
        ({'validated': False}, False),
    )
    @unpack
    @patch.object(user_accessor.UserAccessor, 'find_one')
    def test_is_validated(self, result, is_validated, mock_find):
        accessor = user_accessor.UserAccessor()
        mock_find.return_value = result
        res = accessor.is_validated('username')
        mock_find.assert_called_once_with(
            {'username': 'username'}, {'_id': 0, 'validated': 1})
        self.assertIs(res, is_validated)

    @patch.object(user_accessor.UserAccessor, 'get_paginated_results')
    def test_get_paginated_list(self, get_results):
        get_results.return_value = {'results': [{'field': 'a'}, {'field': 'b'}], 'total': 2}
        results = {'results': ['a', 'b'], 'total': 2}
        accessor = user_accessor.UserAccessor()
        res = accessor.get_paginated_list('username', 'field', 'skip', 'limit', 'sort')
        self.assertEqual(res, results)
        get_results.assert_called_with(
            {'username': 'username'},
            {'_id': 0, 'field': 1},
            '$field', 'skip', 'limit', 'sort'
        )

    def test_get_list(self):
        collection = self.get_collection()
        collection.find_one.return_value = {'field': [1, 2, 3]}
        accessor = user_accessor.UserAccessor()
        res = accessor.get_list('username', 'field')
        collection.find_one.assert_called_with({'username': 'username'}, {'_id': 0, 'field': 1})
        self.assertEqual(res, [1, 2, 3])

    def test_insert_list_item(self):
        collection = self.get_collection()
        accessor = user_accessor.UserAccessor()
        accessor.insert_list_item('username', 'field_name', {'item': 'value'})
        collection.update_one.assert_called_with(
            {'username': 'username'},
            {'$push': {'field_name': {
                '$each': [{'item': 'value'}], '$position': 0
            }}}
        )

    @patch.object(user_accessor.UserAccessor, 'insert_list_item')
    def test_insert_message_item(self, mock_insert):
        accessor = user_accessor.UserAccessor()
        accessor.create_message_item('username', 'file_id', enlargement=1, tile_size=2)
        message = {
            'file_id': 'file_id',
            'enlargement': 1,
            'tile_size': 2,
            'current': 'file_id',
            'progress': 0,
            'message_id': str(self.mock_id.return_value),
            'status': 'queued',
            'expire_at': time.time() + user_accessor.DEFAULT_TIMEOUT,
            'total_frames': 50,
            'frames': []
        }
        mock_insert.assert_called_with('username', 'messages', message)

    @data(
        'gif_data',
        None
    )
    @patch.object(user_accessor.UserAccessor, 'complete_job')
    @patch.object(user_accessor.UserAccessor, 'insert_list_item')
    def test_create_gallery_item(self, gif_data, mock_insert, mock_job):
        accessor = user_accessor.UserAccessor()
        accessor.s3_accessor.insert_image_and_thumbnail.return_value = (1, 2)
        data_type = 'gif_data' if gif_data else 'image_data'

        fn = None if not gif_data else user_accessor.secure_filename(f'{self.mock_id()}.gif')
        res = accessor.create_gallery_item('username', 'image_data', fn, gif_data)
        accessor.s3_accessor.insert_image_and_thumbnail.assert_called_with(
            data_type, filename=fn
        )
        mock_insert.assert_called_once()
        mock_job.assert_called_with('username')
        self.assertEqual(res.get('username'), 'username')
        self.assertEqual(len(res.get('file_ids')), 4)

    @patch.object(user_accessor.UserAccessor, 'insert_list_item')
    def test_upload_file(self, mock_insert):
        img = MagicMock()
        img.filename = 'fn'
        img.read.return_value = b'content'
        self.s3_accessor.return_value.insert_image_and_thumbnail.return_value = ('file_id', 'thumbnail_id')
        path = user_accessor.secure_filename(f'{self.mock_id.return_value}_fn')
        accessor = user_accessor.UserAccessor()
        res = accessor.upload_file('username', img)
        accessor.s3_accessor.insert_image_and_thumbnail.assert_called_once_with(b'content', filename=path)
        self.assertEqual(res, {'img_path': path, 'file_id': 'file_id', 'thumbnail_id': 'thumbnail_id'})
        mock_insert.assert_called_once()

    @data(0, 1)
    def test_create_user(self, count):
        accessor = user_accessor.UserAccessor()
        collection = self.get_collection()
        collection.count.return_value = count
        if count:
            self.assertRaises(user_accessor.UserException, accessor.create_user, 'username', 'email', 'pswd')
            collection.insert_one.assert_not_called()
        else:
            accessor.create_user('username', 'email', 'pswd')
            collection.insert_one.assert_called_once()

    def test_get_pending(self):
        message = [{'message': 'value'}]
        pipeline = [
            {'$match': {'username': 'username'}},
            {'$project': {'message': {'$arrayElemAt': ['$messages', 0]}}},
            {'$project': {
                'message.file_id': 1,
                '_id': 0,
                'message.message_id': 1,
                'message.progress': 1,
                'message.expire_at': 1,
            }}
        ]
        accessor = user_accessor.UserAccessor()
        collection = self.get_collection()
        collection.aggregate.return_value = message
        res = accessor.get_pending_json('username')
        collection.aggregate.assert_called_with(pipeline)
        self.assertEqual(res, 'value')

    def test_get_pending_frame(self):
        message = [{'message': 'value'}]
        pipeline = [
            {'$match': {'username': 'username'}},
            {'$project': {'message': {'$arrayElemAt': ['$messages', 0]}}},
            {'$project': {
                'message.file_id': 1,
                '_id': 0,
                'message.frame': {'$arrayElemAt': ['$message.frames', 0]}
            }}
        ]
        accessor = user_accessor.UserAccessor()
        collection = self.get_collection()
        collection.aggregate.return_value = message
        res = accessor.get_pending_frame('username')
        collection.aggregate.assert_called_with(pipeline)
        self.assertEqual(res, 'value')

    def test_complete_job(self):
        accessor = user_accessor.UserAccessor()
        accessor.complete_job('username')
        to_update = {'$set': {
            'messages.0.progress': 1.0,
            'messages.0.status': 'complete'},
            '$push': {'messages.0.frames': {'$each': [], '$slice': -1}}}
        collection = self.get_collection()
        collection.update_one.assert_called_with({'username': 'username'}, to_update)

    def test_validate_user(self):
        accessor = user_accessor.UserAccessor()
        accessor.validate_user('username')
        to_update = {'$set': {'validated': True}}
        collection = self.get_collection()
        collection.update_one.assert_called_with({'username': 'username'}, to_update)

    @staticmethod
    @patch.object(user_accessor.UserAccessor, 'get_array_element')
    def test_get_gallery_item(get_element):
        accessor = user_accessor.UserAccessor()
        accessor.get_gallery_item('gallery_id', 'username')
        get_element.assert_called_with(
            {'username': 'username'}, 'gallery', {'gallery.gallery_id': 'gallery_id'}
        )

    @staticmethod
    @patch.object(user_accessor.UserAccessor, 'get_array_element')
    def test_get_upload_item(get_element):
        accessor = user_accessor.UserAccessor()
        accessor.get_upload_item('file_id', 'username')
        get_element.assert_called_with(
            {'username': 'username'}, 'uploads', {'uploads.file_id': 'file_id'}
        )

    @patch.object(user_accessor.UserAccessor, 'delete_one_element')
    @patch.object(user_accessor.UserAccessor, 'get_gallery_item')
    def test_delete_gallery_item(self, mock_get_item, mock_delete):
        mock_get_item.return_value = {'file_ids': [1, 1, 2, 2]}
        accessor = user_accessor.UserAccessor()
        accessor.delete_gallery_item('gallery_id', 'username')
        mock_get_item.assert_called_with('gallery_id', 'username')
        accessor.s3_accessor.delete_object.assert_any_call(1, 'media_bucket')
        accessor.s3_accessor.delete_object.assert_any_call(2, 'media_bucket')
        mock_delete.assert_called_once_with(
            {'username': 'username'},
            'gallery',
            {'gallery_id': 'gallery_id'}
        )
        self.assertEqual(accessor.s3_accessor.delete_object.call_count, 2)

    @patch.object(user_accessor.UserAccessor, 'delete_one_element')
    @patch.object(user_accessor.UserAccessor, 'get_upload_item')
    def test_delete_uploads_item(self, mock_get_item, mock_delete):
        mock_get_item.return_value = {'file_id': 1, 'thumbnail_id': 2}
        accessor = user_accessor.UserAccessor()
        accessor.delete_upload_item('file_id', 'username')
        mock_get_item.assert_called_with('file_id', 'username')
        accessor.s3_accessor.delete_object.assert_any_call(1, 'media_bucket')
        accessor.s3_accessor.delete_object.assert_any_call(2, 'media_bucket')
        mock_delete.assert_called_once_with(
            {'username': 'username'},
            'uploads',
            {'file_id': 'file_id'}
        )
        self.assertEqual(accessor.s3_accessor.delete_object.call_count, 2)

    @patch.object(user_accessor.UserAccessor, 'find_one')
    def test_delete_user(self, mock_find):
        mock_find.return_value = {
            'gallery': [{'file_ids': [1, 2, 3]}, {'file_ids': [4, 5]}],
            'uploads': [{'file_id': 6, 'thumbnail_id': 7}]
        }
        accessor = user_accessor.UserAccessor()
        accessor.delete_user('username')
        mock_find.assert_called_once_with({'username': 'username'})
        self.assertEqual(accessor.s3_accessor.delete_object.call_count, 7)

if __name__ == '__main__':
    unittest.main()
