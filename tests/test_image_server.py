import unittest
from tests.utilities import BaseTest
from helpers.image_server import ImageServer
from ddt import data, ddt, unpack


@ddt
class TestImageServer(BaseTest):
    import_route = 'helpers.image_server'

    def setUp(self):
        self.mock_streamer = self.add_patcher('ImageStreamer').return_value
        self.mock_s3 = self.add_patcher('S3Accessor').return_value
        self.mock_grid_fs = self.add_patcher('GridFsAccessor').return_value
        self.mock_response = self.add_patcher('make_response')
        self.mock_env = self.add_patcher('Environment').return_value
        self.mock_env.media_bucket = 'media_bucket'
        self.mock_decode = self.add_patcher('decode_image_data')

    def test_serve_from_mongodb(self):
        mock_img = self.mock_grid_fs.get.return_value
        content = b'image_content'
        mock_img.read.return_value = content
        mock_img.mimetype = 'image/type'
        resp = ImageServer().serve_from_mongodb('file_id')
        self.mock_grid_fs.get.assert_called_with('file_id')
        self.assertEqual(resp.content_type, 'image/type')
        self.mock_response.assert_called_with(content)

    @data(
        (None, 'media_bucket'),
        ('bucket', 'bucket'),
        ('bucket', 'bucket'),
    )
    @unpack
    def test_serve_from_s3(self, bucket, exp_bucket):
        mock_img = self.mock_s3.get.return_value
        content = b'image_content'
        mock_img.read.return_value = content
        mock_img.mimetype = 'image/type'
        resp = ImageServer.serve_from_s3('file_id', bucket)
        self.mock_s3.get.assert_called_with('file_id', bucket_name=exp_bucket)
        self.assertEqual(resp.content_type, 'image/type')
        self.mock_response.assert_called_with(content)

    @data(
        'image/gif',
        'image/jpg'
    )
    def test_serve_from_string(self, mimetype):
        content = b'image_content'
        self.mock_decode.return_value = content
        resp = ImageServer.serve_from_string('image_string', mimetype)
        self.mock_decode.assert_called_with('image_string')
        self.assertEqual(resp.content_type, mimetype)
        self.mock_response.assert_called_with(content)


if __name__ == '__main__':
    unittest.main()
