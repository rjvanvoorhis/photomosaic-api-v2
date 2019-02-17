import unittest
from tests.utilities import BaseTest
from accessors import grid_fs_accessor
from ddt import ddt, data, unpack


@ddt
class TestGridFsAccessor(BaseTest):
    import_route = 'accessors.grid_fs_accessor'

    def setUp(self):
        self.mock_env = self.add_patcher('Environment').return_value
        self.mock_env.mongodb_uri = 'mongodb://my_host:27017/'
        self.mock_client = self.add_patcher('MongoClient')
        self.mock_gridfs = self.add_patcher('gridfs')
        self.mock_streamer = self.add_patcher('ImageStreamer').return_value
        self.mock_client.return_value.photomosaic = 'default_db'
        self.fs = self.mock_gridfs.GridFS.return_value
        self.mock_logger = self.add_patcher('logging').getLogger.return_value
        self.mock_uuid = self.add_patcher('uuid4')
        self.mock_uuid.return_value = 'mock_id'

    @data(
        ('custom', 'custom', 'mongodb://custom:27017/', 'mongodb://custom:27017/'),
        (None, 'default_db', 'mongodb://custom:27017/', 'mongodb://custom:27017/'),
    )
    @unpack
    def test_init(self, db, exp_db, uri, exp_uri):
        self.mock_env.mongodb_uri = uri
        fs = grid_fs_accessor.GridFsAccessor(db=db)
        self.assertEqual(fs.db, exp_db)
        self.assertEqual(fs.uri, exp_uri)
        self.mock_gridfs.GridFS.assert_called_with(exp_db)

    def test_get(self):
        fs = grid_fs_accessor.GridFsAccessor()
        self.fs.get.return_value = 'data'
        res = fs.get('file_id')
        self.fs.get.assert_called_with('file_id')
        self.assertEqual(res, 'data')

    def test_put(self):
        fs = grid_fs_accessor.GridFsAccessor()
        self.fs.put.return_value = 'file_id'
        res = fs.put('data', kwarg_1='a', kwarg_2='b')
        self.fs.put.assert_called_with('data', kwarg_1='a', kwarg_2='b')
        self.assertEqual(res, 'file_id')
        self.mock_logger.debug.assert_called_with('Saved file with file_id: file_id')

    def test_find(self):
        fs = grid_fs_accessor.GridFsAccessor()
        self.fs.find_one.return_value = 'data'
        res = fs.find_one('query', 'session', 'arg', bar='bar')
        self.fs.find_one.assert_called_with('arg', filter='query', session='session', bar='bar')
        self.assertEqual(res, 'data')

    def test_delete(self):
        grid_fs_accessor.GridFsAccessor().delete('file_id')
        self.fs.delete.assert_called_with('file_id')
        self.mock_logger.debug.assert_called_with('Removing file with file_id: file_id')


    @data(
        (None, grid_fs_accessor.secure_filename('mock_fn')),
        ('custom', grid_fs_accessor.secure_filename('custom'))
    )
    @unpack
    def test_insert_image_and_thumbnail(self, fn, expected_fn):
        content = b'image_content'
        self.mock_streamer.load.return_value.dump.return_value = {
            'image': content, 'filename': 'mock_fn', 'mimetype': 'mime', 'thumbnail': 'mock_thumbnail'}
        grid_fs_accessor.GridFsAccessor().insert_image_and_thumbnail(content, fn)
        self.mock_streamer.load.assert_called_with(content)
        self.fs.put.assert_any_call(content, _id='mock_id', filename=expected_fn, mimetype='mime')
        self.fs.put.assert_any_call(
            'mock_thumbnail', _id='mock_id', filename=f'thumbnail_{expected_fn}', mimetype='mime'
        )


if __name__ == '__main__':
    unittest.main()
