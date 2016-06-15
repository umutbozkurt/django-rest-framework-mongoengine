# mockup for PIL for testing purposes
try:
    from unittest import mock  # NOQA
except ImportError:
    import mock  # NOQA

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
