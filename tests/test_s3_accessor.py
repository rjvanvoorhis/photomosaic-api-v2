import unittest
from tests.utilities import BaseTest
from accessors import s3_accessor
from ddt import ddt, data, unpack
from mock import MagicMock, patch

@ddt
class TestS3Accessor(BaseTest):
    import_route = 'accessors.s3_accessor'

    def setUp(self):
        self.mock_env = self.add_patcher('Environment').return_value
        self.mock_boto = self.add_patcher('boto3')
        self.mock_streamer = self.add_patcher('ImageStreamer').return_value
        self.mock_logger = self.add_patcher('logging').getLogger.return_value
        self.mock_uuid = self.add_patcher('uuid4')
        self.mock_uuid.return_value = 'mock_id'


        self.mock_env.s3_endpoint_url = 's3_endpoint'
        self.mock_env.aws_access_key_id = 'key_id'
        self.mock_env.aws_secret_access_key = 'access_key'
        self.mock_env.media_bucket = 'media_bucket'

    @staticmethod
    def get_accessor():
        return s3_accessor.S3Accessor()

    def test_create_bucket(self):
        accessor = self.get_accessor()
        accessor.create_bucket('bucket_name')
        accessor.client.create_bucket.assert_called_with(Bucket='bucket_name', ACL='public-read')


    @data(
        ('application/image', 'application/image', 'bucket', 'bucket'),
        (None, 'application/octet-stream', None, 'media_bucket'),
    )
    @unpack
    def test_put(self, mime, exp_mime, bucket, exp_bucket):
        accessor = self.get_accessor()
        accessor.put(b'content', bucket_name=bucket, mimetype=mime, filename='fn')
        accessor.client.put_object.assert_called_with(
            Body=b'content',
            Key='mock_id',
            Bucket=exp_bucket,
            ContentType=exp_mime,
            Metadata={'mimetype': exp_mime, 'filename': 'fn'}
        )

    @data(
        (None, 'media_bucket'),
        ('bucket', 'bucket')
    )
    @unpack
    def test_get(self, bucket, exp_bucket):
        accessor = self.get_accessor()
        obj = MagicMock()
        obj.get.return_value = {'filename': 'fn', 'mimetype': 'mime'}
        accessor.client.get_object.return_value = obj
        res = accessor.get('file_id', bucket)
        accessor.client.get_object.assert_called_with(Key='file_id', Bucket=exp_bucket)
        self.assertEqual(res.mimetype, 'mime')
        self.assertEqual(res.filename, 'fn')

    def test_insert_image_and_thumbnail(self):
        accessor = self.get_accessor()
        method = accessor.put
        accessor.put = MagicMock()
        accessor.insert_image_and_thumbnail(b'content')
        accessor.streamer.load.assert_called_with(b'content')
        self.assertEqual(accessor.put.call_count, 2)
        accessor.put = method

    @data(
        ('bucket', 'bucket'),
        (None, 'media_bucket')
    )
    @unpack
    def test_delete_object(self, bucket, exp_bucket):
        accessor = self.get_accessor()
        accessor.delete_object('file_id', bucket_name=bucket)
        accessor.resource.Object.assert_called_with(exp_bucket, 'file_id')

    def test_delete_bucket(self):
        accessor = self.get_accessor()
        accessor.delete_bucket('bucket')
        bucket = accessor.resource.Bucket.return_value
        accessor.resource.Bucket.assert_called_with('bucket')
        bucket.objects.all.return_value.delete.assert_called_once()
        bucket.delete.assert_called_once()

    @data(
        True, False
    )
    def test_health(self, exp_result):
        accessor = self.get_accessor()
        accessor.client.head_bucket.side_effect = None if exp_result else Exception('Oh no!')
        res = accessor.health()
        if not exp_result:
            accessor.logger.exception.assert_called_with('Oh no!')
        self.assertIs(res, exp_result)

if __name__ == '__main__':
    unittest.main()