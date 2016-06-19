from __future__ import unicode_literals

import os
pwd = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

try:
    from unittest import mock  # NOQA
except ImportError:
    import mock  # NOQA

from django.test import TestCase
from django.core.files.uploadedfile import UploadedFile
from mongoengine import Document, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent

from . import mockpil
import sys
sys.modules['PIL'] = mockpil
fields.Image = mockpil.Image
fields.ImageOps = mockpil.ImageOps


class FileDoc(Document):
    image = fields.ImageField(collection_name='images')


class TestSerializer(DocumentSerializer):
    class Meta:
        model = FileDoc


class TestFilesMapping(TestCase):
    def test_mapping(self):
        class FileDoc(Document):
            f = fields.FileField(collection_name='files')
            i = fields.ImageField(collection_name='images')

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = FileDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                f = FileField(required=False)
                i = ImageField(required=False)
        """)

        assert unicode_repr(TestSerializer()) == expected


class TestFilesIntegration(TestCase):
    """ operational test
    Test if primary methods work.
    """
    def setUp(self):
        self.files = [open(pwd + "cat1.jpg", "rb"), open(pwd + "cat2.jpg", "rb")]
        self.uploads = [UploadedFile(f, f.name, "image/jpeg", os.path.getsize(f.name)) for f in self.files]

    def tearDown(self):
        FileDoc.drop_collection()
        FileDoc._get_db().drop_collection('files')
        for f in self.files:
            f.close()

    def test_parse(self):
        data = {'image': self.uploads[0]}
        serializer = TestSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        expected = {
            'image': None
        }
        assert serializer.data == expected

    def test_retrieve(self):
        instance = FileDoc.objects.create(image=self.files[0])

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'image': str(instance.image.grid_id),
        }
        assert serializer.data == expected

    def test_create(self):
        data = {'image': self.uploads[0]}
        serializer = TestSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()

        assert isinstance(instance.image, fields.GridFSProxy)
        assert instance.image.length == self.uploads[0].size

        expected = {
            'id': str(instance.id),
            'image': str(instance.image.grid_id)
        }
        assert serializer.data == expected

    def test_update(self):
        instance = FileDoc.objects.create(image=self.files[0])
        data = {'image': self.uploads[1]}

        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance.image, fields.GridFSProxy)
        assert instance.image.length == self.uploads[1].size

        expected = {
            'id': str(instance.id),
            'image': str(instance.image.grid_id)
        }
        assert serializer.data == expected
