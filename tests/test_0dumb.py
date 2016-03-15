""" These are snippets to creatte other tests """

from __future__ import unicode_literals

import pytest
from django.test import TestCase
from mongoengine import Document, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class DumbModel(Document):
    name = fields.StringField()


@pytest.mark.skipif(True, reason="dumb")
class TestMapping(TestCase):
    """ field mapping test
    Testif model fields are recognized and created in serializer.
    """
    def test_mapping(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = DumbModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)


@pytest.mark.skipif(True, reason="dumb")
class TestIntegration(TestCase):
    """ operational test
    Test if primary methods work.
    """
    def tearDown(self):
        DumbModel.drop_collection()

    def test_retrival(self):
        instance = DumbModel.objects.create(foo="Foo")

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = DumbModel

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': "Foo"
        }

        self.assertEqual(serializer.data, expected)

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = DumbModel

        data = {
            'foo': "Foo"
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.foo == "Foo"

        expected = {
            'id': str(instance.id),
            'foo': "Foo"
        }
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = DumbModel.objects.create(foo="Foo")

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = DumbModel

        data = {
            'foo': "Bar"
        }

        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.foo == "Bar"

        expected = {
            'id': str(instance.id),
            'foo': "Bar"
        }
        self.assertEqual(serializer.data, expected)
