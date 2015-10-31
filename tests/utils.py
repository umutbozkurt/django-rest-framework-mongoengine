from bson import DBRef

from mongoengine.errors import DoesNotExist


def dedent(blocktext):
    return '\n'.join([line[12:] for line in blocktext.splitlines()[1:-1]])


class MockObject(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __str__(self):
        kwargs_str = ', '.join([
            '%s=%s' % (key, value)
            for key, value in sorted(self._kwargs.items())
        ])
        return '<MockObject %s>' % kwargs_str

    def to_dbref(self):
        return DBRef('mock_collection', self.id)

class MockQueryset(object):
    def __init__(self, iterable):
        self.items = iterable

    def only(self, *args):
        return self

    def get(self, **lookup):
        for item in self.items:
            if all([
                getattr(item, key, None) == value
                for key, value in lookup.items()
            ]):
                return item
        raise DoesNotExist()

class BadType(object):
    """
    When used as a lookup with a `MockQueryset`, these objects
    will raise a `TypeError`, as occurs in Django when making
    queryset lookups with an incorrect type for the lookup value.
    """
    def __eq__(self):
        raise TypeError()
