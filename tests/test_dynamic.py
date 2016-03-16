from __future__ import unicode_literals

from django.test import TestCase
from rest_framework import fields as drf_fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DynamicDocumentSerializer

from .utils import dedent
from .models import DumbDynamic


class TestDynamicMapping(TestCase):
    def test_declared(self):
        class TestSerializer(DynamicDocumentSerializer):
            class Meta:
                model = DumbDynamic

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
                foo = IntegerField(required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_extended(self):
        class TestSerializer(DynamicDocumentSerializer):
            bar = drf_fields.CharField(required=False)

            class Meta:
                model = DumbDynamic

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                bar = CharField(required=False)
                name = CharField(required=False)
                foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected


class DynamicSerializer(DynamicDocumentSerializer):
    class Meta:
        model = DumbDynamic


class TestDynamicIntegration(TestCase):
    def tearDown(self):
        DumbDynamic.drop_collection()

    def test_retrival(self):
        instance = DumbDynamic.objects.create(foo=42, bar=43, baz="Baz")
        serializer = DynamicSerializer(instance)
        expected = {
            'id': str(instance.id),
            'name': None,
            'foo': 42,
            'bar': 43,
            'baz': "Baz"
        }
        assert serializer.data == expected

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
            'name': None,
            'foo': 42,
            'bar': 43,
            'baz': "Baz"
        }
        assert serializer.data == expected

    def test_update(self):
        instance = DumbDynamic.objects.create(foo=42, bar=43, baz="z")

        data = {'foo': 142, 'bar': 143, 'baz': "Baz"}

        serializer = DynamicSerializer(instance, data=data)
        assert serializer.is_valid()

        instance = serializer.save()
        assert instance.foo == 142
        assert instance.bar == 143
        assert instance.baz == "Baz"

        expected = {
            'id': str(instance.id),
            'name': None,
            'foo': 142,
            'bar': 143,
            'baz': "Baz"
        }
        assert serializer.data == expected
