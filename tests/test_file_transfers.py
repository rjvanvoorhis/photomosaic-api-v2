import unittest
from tests.utilities import BaseTest
from ddt import ddt, data, unpack
from helpers import file_transfers
from mock import patch

@ddt
class FileTransferTestCase(BaseTest):
    import_route = 'helpers.file_transfers'

    def setUp(self):
        self.mock_image = self.add_patcher('Image')
        self.mock_subprocess = self.add_patcher('subprocess')
        self.mock_os = self.add_patcher('os')
        self.add_freeze('2012-04-14 10:00:00')
        self.mock_open = self.add_patcher('open', import_route='builtins')
        self.cm = self.mock_open.return_value
        self.base_fp = '13343976000'

    def load_context(self, mock_data):
        self.cm.__enter__.return_value.read.return_value = mock_data

    @data(
        (None, 'jpg'),
        ('jpg', 'jpg'),
        ('gif', 'gif')
    )
    @unpack
    def test_make_file_path(self, ext, expected_ext):
        expected = f'{self.base_fp}.{expected_ext}'
        self.assertEqual(expected, file_transfers.make_file_path(ext))

    def test_data_transform(self):
        start_string = 'Myteststring\n'
        bytes_data = file_transfers.decode_image_data(start_string)
        self.assertIsInstance(bytes_data, bytes)
        result = file_transfers.encode_image_data(bytes_data)
        self.assertEqual(result, 'Myteststring\n')

    def test_load_gif_thumbnail(self):
        mock_data = b'some_mock_data'
        exp_path = f'{self.base_fp}.gif'
        self.cm.__enter__.return_value.read.return_value = mock_data
        exp_cmd = f'gifsicle -b {exp_path} --resize-fit 300x300'
        file_transfers.ImageStreamer().load_gif_thumbnail(mock_data)
        self.mock_open.assert_any_call(exp_path, 'rb')
        self.mock_open.assert_any_call(exp_path, 'wb')
        self.load_context(mock_data)
        self.assertEqual(self.cm.__exit__.call_count, 2)
        self.mock_subprocess.run.assert_called_with(exp_cmd, shell=True)

    @patch('helpers.file_transfers.BytesIO')
    def test_flush(self, mock_bytes):
        streamer = file_transfers.ImageStreamer()
        streamer.flush()
        streamer.image.close.assert_called()
        streamer.thumbnail.close.assert_called()
        self.assertEqual(mock_bytes.call_count, 4)

    @data(
        ('gif', 'gif'),
        (None, 'jpg'),
        ('jpg', 'jpg')
    )
    @unpack
    @patch.object(file_transfers.ImageStreamer, 'load_gif_thumbnail')
    def test_load(self, img_format, exp_format, mock_load_thumbnail):
        mock_data = b'mock_data'
        mock_img = self.mock_image.open.return_value
        mock_img.format = img_format
        res = file_transfers.ImageStreamer().load(mock_data)
        self.assertEqual(res.image_format, exp_format)
        if img_format == 'gif':
            mock_load_thumbnail.assert_called_with(mock_data)
        else:
            mock_img.thumbnail.assert_called_with((300, 300))
            mock_img.save.assert_called_with(res.thumbnail, exp_format)

    @data(
        'jpg',
        'gif'
    )
    @patch.object(file_transfers.ImageStreamer, 'flush')
    def test_dump(self, exp_format, mock_flush):
        exp_fp = f'{self.base_fp}.{exp_format}'
        exp_mimetype = f'image/{exp_format}'
        streamer = file_transfers.ImageStreamer()
        streamer.image_format = exp_format
        streamer.image.write(b'mock_image')
        streamer.thumbnail.write(b'mock_thumbnail')
        exp_data = {
            'image': b'mock_image', 'thumbnail': b'mock_thumbnail',
            'mimetype': exp_mimetype,
            'filename': exp_fp,
            'thumbnail_filename': f'thumbnail_{exp_fp}'
        }
        res = streamer.dump()
        mock_flush.assert_called_once()
        self.assertEqual(res, exp_data)


if __name__ == '__main__':
    unittest.main()
