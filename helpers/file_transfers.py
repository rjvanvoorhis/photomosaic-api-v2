import time
import binascii
from io import BytesIO
from PIL import Image
import subprocess
import os
DEFAULT_THUMBNAIL_SIZE = 300


def make_file_path(extension=None):
    extension = extension if extension is not None else 'jpg'
    return f'{str(time.time()).replace(".", "")}.{extension}'


def encode_image_data(image_data):
    return binascii.b2a_base64(image_data).decode()


def decode_image_data(image_string):
    return binascii.a2b_base64(image_string)


class ImageStreamer(object):
    def __init__(self):
        self.image = BytesIO()
        self.thumbnail = BytesIO()
        self.image_format = 'jpg'

    def flush_image(self):
        self.image.close()
        self.image = BytesIO()

    def flush_thumbnail(self):
        self.thumbnail.close()
        self.thumbnail = BytesIO()

    def flush(self):
        self.flush_image()
        self.flush_thumbnail()

    def load(self, img_data):
        self.image.write(img_data)
        self.image.seek(0)
        img = Image.open(self.image)
        if str(img.format).lower() == 'gif':
            self.load_gif_thumbnail(img_data)
            self.image_format = 'gif'
        else:
            img.format = img.format if img.format else 'jpg'
            self.image_format = img.format
            img.thumbnail((DEFAULT_THUMBNAIL_SIZE, DEFAULT_THUMBNAIL_SIZE))
            img.save(self.thumbnail, img.format)
        return self

    def load_gif_thumbnail(self, img_data):
        path = make_file_path('gif')
        with open(path, 'wb') as fn:
            fn.write(img_data)
        cmd = f'gifsicle -b {path} --resize-fit {DEFAULT_THUMBNAIL_SIZE}x{DEFAULT_THUMBNAIL_SIZE}'
        subprocess.run(cmd, shell=True)
        with open(path, 'rb') as fn:
            self.thumbnail.write(fn.read())
        os.remove(path)

    def dump(self):
        self.image.seek(0)
        self.thumbnail.seek(0)
        mimetype = f'image/{self.image_format}'
        filename = make_file_path(self.image_format)
        data = {
                    'image': self.image.read(), 'thumbnail': self.thumbnail.read(),
                    'mimetype': mimetype, 'filename': filename,
                    'thumbnail_filename': f'thumbnail_{filename}'
        }
        self.flush()
        return data
