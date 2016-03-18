# mockup for PIL for testing purposes
from unittest import mock


class Image():
    format = 'jpeg'
    size = (133, 100)
    info = {
        'progressive': False
    }

    def __init__(self, file):
        self.file = file

    @classmethod
    def open(cls, file):
        return Image(file)

    def save(self, io, format, progressive):
        io.write(self.file.read())


ImageOps = mock.Mock()
