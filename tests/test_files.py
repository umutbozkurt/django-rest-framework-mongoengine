from __future__ import unicode_literals

import os
pwd = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

from django.test import TestCase
from django.core.files.utils import FileProxyMixin
from mongoengine import Document, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class FilesModel(Document):
    fil = fields.FileField(collection_name='files')


class TestSerializer(DocumentSerializer):
    class Meta:
        model = FilesModel


class TestMapping(TestCase):
    def test_mapping(self):
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                fil = FileField(required=False)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)


class MockUpload(FileProxyMixin):
    def __init__(self, filename):
        self.name = filename
        self.size = os.path.getsize(filename)
        self.file = open(filename, "rb")


class TestIntegration(TestCase):
    """ operational test
    Test if primary methods work.
    """
    def setUp(self):
        self.file1 = MockUpload(pwd + "cat1.jpg")
        self.file2 = MockUpload(pwd + "cat2.jpg")

    def tearDown(self):
        FilesModel.drop_collection()
        FilesModel._get_db().drop_collection('files')

    def test_retrival(self):
        instance = FilesModel.objects.create(fil=self.file1.file)

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'fil': str(instance.fil.grid_id)
        }
        self.assertEqual(serializer.data, expected)

    def test_create(self):
        data = {'fil': self.file1}
        serializer = TestSerializer(data=data)

        assert serializer.is_valid()

        instance = serializer.save()

        self.assertIsInstance(instance.fil, fields.GridFSProxy)
        self.assertEqual(instance.fil.length, self.file1.size)

        expected = {
            'id': str(instance.id),
            'fil': str(instance.fil.grid_id)
        }
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = FilesModel.objects.create(fil=self.file1.file)
        data = {'fil': self.file2}

        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        self.assertIsInstance(instance.fil, fields.GridFSProxy)
        self.assertEqual(instance.fil.length, self.file2.size)

        expected = {
            'id': str(instance.id),
            'fil': str(instance.fil.grid_id)
        }
        self.assertEqual(serializer.data, expected)
