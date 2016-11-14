""" Snippets to creatte other tests """

from __future__ import unicode_literals

from django.test import TestCase
from rest_framework import fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .models import DumbDocument
from .utils import FieldTest, dedent


class SomeField(fields.IntegerField):
    pass


class TestSomeField(FieldTest, TestCase):
    field = SomeField()
    valid_inputs = {
        123: 123,
        "123": 123
    }
    invalid_inputs = {
        'xxx': ""
    }
    outputs = {
        123: 123
    }


class TestMapping(TestCase):
    """ Field mapping test

    Test if model fields are recognized and created in DocumentSerializer
    """
    def test_mapping(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = DumbDocument
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
                foo = IntegerField(required=False)
        """)

        # better output then self.assertEqual()
        assert unicode_repr(TestSerializer()) == expected


class TestSerializer(DocumentSerializer):
    class Meta:
        model = DumbDocument
        fields = '__all__'


class TestIntegration(TestCase):
    """ Operational test

    Test if all operations performed correctly
    """
    def doCleanups(self):
        DumbDocument.drop_collection()

    def test_parsing(self):
        input_data = {'name': "dumb", 'foo': "123"}
        serializer = TestSerializer(data=input_data)

        assert serializer.is_valid(), serializer.errors

        expected = {'name': "dumb", 'foo': 123}

        assert serializer.validated_data == expected

    def test_retrive(self):
        instance = DumbDocument.objects.create(name="dumb", foo=123)
        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'name': "dumb",
            'foo': 123,
        }

        assert serializer.data == expected

    def test_create(self):
        data = {
            'foo': 123
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.foo == 123

        expected = {
            'id': str(instance.id),
            'name': None,
            'foo': 123,
        }

        assert serializer.data == expected

    def test_update(self):
        instance = DumbDocument.objects.create(foo=123)

        data = {
            'foo': 234
        }

        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.foo == 234

        expected = {
            'id': str(instance.id),
            'foo': 234,
            'name': None
        }

        assert serializer.data == expected
