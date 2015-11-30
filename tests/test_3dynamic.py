from __future__ import unicode_literals

import pytest

from django.test import TestCase

from mongoengine import DynamicDocument, fields

from rest_framework.compat import unicode_repr
from rest_framework import fields as drf_fields

from rest_framework_mongoengine.serializers import DynamicDocumentSerializer

from .utils import dedent


class DynamicModel(DynamicDocument):
    foo = fields.IntField()

class TestDynamicMapping(TestCase):
    def test_dynamic_serializer(self):
        class TestSerializer(DynamicDocumentSerializer):
            class Meta:
                model = DynamicModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                foo = IntegerField(required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_dynamic_serializer_extended(self):
        class TestSerializer(DynamicDocumentSerializer):
            class Meta:
                model = DynamicModel
            bar = drf_fields.CharField(required=False)

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                bar = CharField(required=False)
                foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected



class DynamicSerializer(DynamicDocumentSerializer):
    class Meta:
        model = DynamicModel


class TestDynamicIntegration(TestCase):
    def tearDown(self):
        DynamicModel.drop_collection()

    def test_retrival(self):
        instance = DynamicModel.objects.create(foo=42, bar=43, baz="Baz")
        serializer = DynamicSerializer(instance)
        expected = {
            'id': str(instance.id),
            'foo': 42,
            'bar': 43,
            'baz': "Baz"
        }
        self.assertEqual(serializer.data, expected)

    def test_create(self):
        data = {
            'foo': 42,
            'bar': 43,
            'baz': "Baz"
        }

        serializer = DynamicSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.foo == 42
        assert instance.bar == 43
        assert instance.baz == "Baz"

        expected = {
            'id': str(instance.id),
            'foo': 42,
            'bar': 43,
            'baz': "Baz"
        }
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = DynamicModel.objects.create(foo=42, bar=43, baz="z")

        data = { 'foo': 142, 'bar': 143, 'baz': "Baz" }

        serializer = DynamicSerializer(instance, data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.foo == 142
        assert instance.bar == 143
        assert instance.baz == "Baz"

        expected = {
            'id': str(instance.id),
            'foo': 142,
            'bar': 143,
            'baz': "Baz"
        }
        self.assertEqual(serializer.data, expected)
