from __future__ import unicode_literals

import json

from django.test import TestCase
from rest_framework import fields as drf_fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import (
    DocumentSerializer, DynamicDocumentSerializer, EmbeddedDocumentSerializer
)

from .models import DumbDocument, DumbDynamic, DumbEmbedded, EmbeddingDynamic, DumbDynamicEmbedded, \
    DocumentEmbeddingDynamic
from .utils import dedent


class DumbDocumentSerializer(DocumentSerializer):
    class Meta:
        model = DumbDocument
        fields = '__all__'


class TestDynamicDataIntegration(TestCase):
    """
    Tests that if we pass dynamic data to a DocumentSerializer, they won't
    make it into corresponding Document.
    """
    def doCleanups(self):
        DumbDocument.drop_collection()

    def test_create(self):
        data = {'name': r'Joe', 'foo': 1, 'unexpected': r'data'}

        serializer = DumbDocumentSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

        instance = serializer.save()
        assert instance.name == r'Joe'
        assert instance.foo == 1
        assert not hasattr(instance, 'unexpected')

        expected = {
            'id': str(instance.id),
            'name': r'Joe',
            'foo': 1
        }
        assert serializer.data == expected

    def test_update(self):
        instance = DumbDocument.objects.create(name=u'Joe', foo=1)

        data = {'name': r'Jack', 'foo': 2, 'unexpected': r'data'}

        serializer = DumbDocumentSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.name == r'Jack'
        assert instance.foo == 2
        assert not hasattr(instance, 'unexpected')

        expected = {
            'id': str(instance.id),
            'name': r'Jack',
            'foo': 2
        }
        assert serializer.data == expected


class TestDynamicMapping(TestCase):
    def test_declared(self):
        class TestSerializer(DynamicDocumentSerializer):
            class Meta:
                model = DumbDynamic
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
                foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_extended(self):
        class TestSerializer(DynamicDocumentSerializer):
            bar = drf_fields.CharField(required=False)

            class Meta:
                model = DumbDynamic
                fields = '__all__'

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                bar = CharField(required=False)
                name = CharField(required=False)
                foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected


class TestSerializer(DynamicDocumentSerializer):
    class Meta:
        model = DumbDynamic
        fields = '__all__'


class TestDynamicIntegration(TestCase):
    def doCleanups(self):
        DumbDynamic.drop_collection()

    def test_parsing(self):
        input_data = {
            'foo': 42,
            'bar': 43,
            'baz': "Baz"
        }

        serializer = TestSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            'foo': 42,
            'bar': 43,
            'baz': "Baz"
        }
        assert serializer.validated_data == expected

    def test_retrieval(self):
        instance = DumbDynamic.objects.create(foo=42, bar=43, baz="Baz")
        serializer = TestSerializer(instance)
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

        serializer = TestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

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

        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors

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


# Test that DynamicDocumentSerializer interprets EmbeddedDocumentSerializer
# right.

class DumbEmbeddedSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = DumbEmbedded
        fields = '__all__'


class EmbeddingDynamicSerializer(DynamicDocumentSerializer):
    embedded = DumbEmbeddedSerializer()

    class Meta:
        model = EmbeddingDynamic
        fields = ('name', 'foo', 'embedded')


class TestEmbeddingDynamicMapping(TestCase):
    def test_repr(self):
        expected = dedent("""
            EmbeddingDynamicSerializer():
                name = CharField(required=False)
                foo = IntegerField(required=False)
                embedded = DumbEmbeddedSerializer():
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingDynamicSerializer()) == expected


class TestEmbeddingDynamicIntegration(TestCase):
    data = {
        'name': "Ivan",
        'foo': 42,
        'bar': 43,
        'baz': "Baz",
        'embedded': {
            'name': 'Dumb',
            'foo': 2
        }
    }

    def create_instance(self):
        return EmbeddingDynamic.objects.create(
            name="Ivan",
            foo=42,
            bar=43,
            baz="Baz",
            embedded=DumbEmbedded(name='Dumb', foo=2)
        )

    def test_parsing(self):
        serializer = EmbeddingDynamicSerializer(data=self.data)
        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data == self.data

    def test_retrieval(self):
        instance = self.create_instance()
        serializer = EmbeddingDynamicSerializer(instance)

        assert serializer.data == self.data

    def test_create(self):
        serializer = EmbeddingDynamicSerializer(data=self.data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.name == "Ivan"
        assert instance.foo == 42
        assert instance.bar == 43
        assert instance.baz == "Baz"
        assert instance.embedded.name == "Dumb"
        assert instance.embedded.foo == 2

        assert serializer.data == self.data

    def test_update(self):
        instance = self.create_instance()

        new_data = {
            'name': "Ivan",
            'foo': 142,
            'bar': 143,
            'baz': u"Baz",
            'embedded': {
                'name': 'Bright',
                'foo': 3
            }
        }

        serializer = EmbeddingDynamicSerializer(instance, data=new_data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.foo == 142
        assert instance.bar == 143
        assert instance.baz == "Baz"
        assert instance.embedded.name == 'Bright'
        assert instance.embedded.foo == 3

        # Same JSON data may be represented in different ways in python
        # (dicts/OrderedDicts, unicode/string, different order)
        # so let's just compare JSONs:
        serializer_data_json = json.loads(json.dumps(sorted(serializer.data)))
        new_data_json = json.loads(json.dumps(sorted(new_data)))

        assert serializer_data_json == new_data_json

    def doCleanups(self):
        EmbeddingDynamic.drop_collection()


class DumbDynamicEmbeddedSerializer(EmbeddedDocumentSerializer, DynamicDocumentSerializer):
    class Meta:
        model = DumbDynamicEmbedded
        fields = '__all__'


class DocumentEmbeddingDynamicSerializer(DocumentSerializer):
    embedded = DumbDynamicEmbeddedSerializer()

    class Meta:
        model = DocumentEmbeddingDynamic
        fields = ('name', 'foo', 'embedded')


class TestDocumentEmbeddingDynamicMapping(TestCase):
    def test_repr(self):
        expected = dedent("""
            DocumentEmbeddingDynamicSerializer():
                name = CharField(required=False)
                foo = IntegerField(required=False)
                embedded = DumbDynamicEmbeddedSerializer():
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
        """)
        assert unicode_repr(DocumentEmbeddingDynamicSerializer()) == expected


class TestDocumentEmbeddingDynamicIntegration(TestCase):
    data = {
        'name': 'Ivan',
        'foo': 42,
        'embedded': {
            'name': 'Dumb',
            'foo': 2,
            'bar': 43,
            'baz': 'Baz',
        },
    }

    def create_instance(self):
        return DocumentEmbeddingDynamic.objects.create(
            name='Ivan',
            foo=42,
            embedded=DumbDynamicEmbedded(name='Dumb', foo=2, bar=43, baz='Baz')
        )

    def test_parsing(self):
        serializer = DocumentEmbeddingDynamicSerializer(data=self.data)
        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data == self.data

    def test_retrieval(self):
        instance = self.create_instance()
        serializer = DocumentEmbeddingDynamicSerializer(instance)

        assert serializer.data == self.data

    def test_create(self):
        serializer = DocumentEmbeddingDynamicSerializer(data=self.data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.name == 'Ivan'
        assert instance.foo == 42
        assert instance.embedded.name == 'Dumb'
        assert instance.embedded.foo == 2
        assert instance.embedded.bar == 43
        assert instance.embedded.baz == 'Baz'

    def test_update(self):
        instance = self.create_instance()

        new_data = {
            'name': 'Ivan',
            'foo': 142,
            'embedded': {
                'name': 'Bright',
                'foo': 3,
                'bar': 143,
            },
        }

        serializer = DocumentEmbeddingDynamicSerializer(instance, data=new_data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.name == 'Ivan'
        assert instance.foo == 142
        assert instance.embedded.name == 'Bright'
        assert instance.embedded.foo == 3
        assert instance.embedded.bar == 143
        assert not hasattr(instance.embedded, 'baz')

        serializer_data_json = json.loads(json.dumps(sorted(serializer.data)))
        new_data_json = json.loads(json.dumps(sorted(new_data)))

        assert serializer_data_json == new_data_json

    def doCleanups(self):
        DocumentEmbeddingDynamic.drop_collection()