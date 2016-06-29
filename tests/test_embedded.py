from collections import OrderedDict

import pytest
from django.test import TestCase
from mongoengine import Document, EmbeddedDocument, fields
from rest_framework import fields as drf_fields
from rest_framework.compat import unicode_repr
from rest_framework.serializers import Field, Serializer

from rest_framework_mongoengine.fields import DocumentField
from rest_framework_mongoengine.serializers import (
    DocumentSerializer, EmbeddedDocumentSerializer
)

from .models import DumbEmbedded, OtherEmbedded
from .utils import dedent


class NestedEmbeddedDoc(EmbeddedDocument):
    name = fields.StringField()
    embedded = fields.EmbeddedDocumentField(DumbEmbedded)


class SelfEmbeddingDoc(EmbeddedDocument):
    name = fields.StringField()
    embedded = fields.EmbeddedDocumentField('self')


class EmbeddingDoc(Document):
    embedded = fields.EmbeddedDocumentField(DumbEmbedded)


class NestedEmbeddingDoc(Document):
    embedded = fields.EmbeddedDocumentField(NestedEmbeddedDoc)


class RequiredEmbeddingDoc(Document):
    embedded = fields.EmbeddedDocumentField(DumbEmbedded, required=True)


class ListEmbeddingDoc(Document):
    embedded_list = fields.EmbeddedDocumentListField(DumbEmbedded)


class RecursiveEmbeddingDoc(Document):
    embedded = fields.EmbeddedDocumentField(SelfEmbeddingDoc)


class GenericEmbeddingDoc(Document):
    embedded = fields.GenericEmbeddedDocumentField()


class TestEmbeddingMapping(TestCase):
    def test_embbedded(self):
        class TestSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = DumbEmbedded
        expected = dedent("""
            TestSerializer():
                name = CharField(required=False)
                foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
                depth = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_nodepth(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
                depth = 0
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_restricted(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
                depth_embedding = 1
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = HiddenField(default=None, required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_recursive(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        embedded = EmbeddedSerializer(required=False):
                            name = CharField(required=False)
                            embedded = EmbeddedSerializer(required=False):
                                name = CharField(required=False)
                                embedded = EmbeddedSerializer(required=False):
                                    name = CharField(required=False)
                                    embedded = HiddenField(default=None, required=False)
        """)

        serializer = TestSerializer()
        assert unicode_repr(serializer) == expected

    def test_embedding_recursive_restricted(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingDoc
                depth_embedding = 2
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        embedded = HiddenField(default=None, required=False)
        """)

        serializer = TestSerializer()
        assert unicode_repr(serializer) == expected

    def test_embedding_nested(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_list(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ListEmbeddingDoc
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded_list = EmbeddedSerializer(many=True, required=False):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_required(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RequiredEmbeddingDoc
        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=True):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_generic(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = GenericEmbeddingDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = GenericEmbeddedDocumentField(model_field=<mongoengine.fields.GenericEmbeddedDocumentField: embedded>, required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_custom_generic(self):

        class CustomEmbedding(DocumentField):
            pass

        class TestSerializer(DocumentSerializer):
            serializer_embedded_generic = CustomEmbedding

            class Meta:
                model = GenericEmbeddingDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = CustomEmbedding(model_field=<mongoengine.fields.GenericEmbeddedDocumentField: embedded>, required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_custom_nested(self):
        class CustomTestSerializer(Serializer):
            bla = drf_fields.CharField()

        class TestSerializer(DocumentSerializer):
            serializer_embedded_nested = CustomTestSerializer

            class Meta:
                model = NestedEmbeddingDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    bla = CharField()
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_embedding_custom_bottom(self):
        class CustomEmbedding(Field):
            bla = drf_fields.CharField()

        class TestSerializer(DocumentSerializer):
            serializer_embedded_bottom = CustomEmbedding

            class Meta:
                model = NestedEmbeddingDoc
                depth_embedding = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                embedded = CustomEmbedding(default=None, required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected


class EmbeddingSerializer(DocumentSerializer):
    class Meta:
        model = EmbeddingDoc


class NestedEmbeddingSerializer(DocumentSerializer):
    class Meta:
        model = NestedEmbeddingDoc


class TestEmbeddedIntegration(TestCase):
    """ should work on isolated embedded docs """
    def test_retrieve(self):
        """ serializing standalone doc """
        class TestSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = OtherEmbedded

        instance = OtherEmbedded(name="qwe", bar=123)
        serializer = TestSerializer(instance)

        assert serializer.data == OrderedDict([('name', "qwe"), ('bar', 123)])

    def test_create(self):
        """ creating standalone instance """
        class TestSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = OtherEmbedded

        data = {'name': "qwe", 'bar': 123}

        serializer = TestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance, OtherEmbedded)
        assert instance.name == "qwe"
        assert instance.bar == 123

    def test_update(self):
        """ updating standalone instance with partial data """
        class TestSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = OtherEmbedded
        instance = OtherEmbedded(name="qwe", bar=123)
        data = {'bar': 234}

        serializer = TestSerializer(instance, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert isinstance(instance, OtherEmbedded)
        assert instance.name == "qwe"
        assert instance.bar == 234


class TestEmbeddingIntegration(TestCase):
    def tearDown(self):
        EmbeddingDoc.drop_collection()

    def test_retrieve(self):
        instance = EmbeddingDoc.objects.create(
            embedded=DumbEmbedded(name="Foo")
        )

        serializer = EmbeddingSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((('name', "Foo"), ('foo', None))),
        }
        assert serializer.data == expected

    def test_create(self):
        data = {
            'embedded': {'name': "emb"}
        }

        serializer = EmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance.embedded, DumbEmbedded)
        assert instance.embedded.name == "emb"

        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((('name', "emb"), ('foo', None))),
        }
        assert serializer.data == expected

    def test_update(self):
        instance = EmbeddingDoc.objects.create(
            embedded=DumbEmbedded(name="emb", foo=123)
        )

        data = {
            'embedded': {'foo': 321}
        }
        serializer = EmbeddingSerializer(instance, data=data)

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance.embedded, DumbEmbedded)
        assert instance.embedded.name is None
        assert instance.embedded.foo == 321

        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((('name', None), ('foo', 321))),
        }
        assert serializer.data == expected

    @pytest.mark.skipif(True, reason="TODO")
    def test_update_partial(self):
        pass


class TestNestedEmbeddingIntegration(TestCase):
    def doCleanups(self):
        NestedEmbeddingDoc.drop_collection()

    def test_retrieve(self):
        instance = NestedEmbeddingDoc.objects.create(
            embedded=NestedEmbeddedDoc(
                name='Foo',
                embedded=DumbEmbedded(name="Bar")
            )
        )

        serializer = NestedEmbeddingSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((
                ('name', "Foo"),
                ('embedded', OrderedDict((
                    ('name', "Bar"),
                    ('foo', None)
                )))
            )),
        }
        assert serializer.data == expected

    def test_create(self):
        data = {
            'embedded': {
                'name': 'Foo',
                'embedded': {'name': "emb"}
            }
        }

        serializer = NestedEmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance.embedded, NestedEmbeddedDoc)
        assert instance.embedded.name == "Foo"
        assert isinstance(instance.embedded.embedded, DumbEmbedded)
        assert instance.embedded.embedded.name == 'emb'
        assert instance.embedded.embedded.foo is None

        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((
                ('name', "Foo"),
                ('embedded', OrderedDict((('name', "emb"), ('foo', None))))
            )),
        }
        assert serializer.data == expected

    def test_update(self):
        instance = NestedEmbeddingDoc.objects.create(
            embedded=NestedEmbeddedDoc(
                name='Foo',
                embedded=DumbEmbedded(name="Bar")
            )
        )

        data = {
            'embedded': {
                'name': 'Bar',
                'embedded': {"foo": 321}
            }
        }

        serializer = NestedEmbeddingSerializer(instance, data=data)

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance.embedded, NestedEmbeddedDoc)
        assert instance.embedded.name == "Bar"
        assert isinstance(instance.embedded.embedded, DumbEmbedded)
        assert instance.embedded.embedded.name is None
        assert instance.embedded.embedded.foo == 321

        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((
                ('name', 'Bar'),
                ('embedded', OrderedDict((
                    ('name', None),
                    ('foo', 321)
                )))
            )),
        }
        assert serializer.data == expected

    @pytest.mark.skipif(True, reason="TODO")
    def test_update_partial(self):
        pass


class ListEmbeddingSerializer(DocumentSerializer):
    class Meta:
        model = ListEmbeddingDoc


class TestListEmbeddingIntegration(TestCase):
    def doCleanups(self):
        ListEmbeddingDoc.drop_collection()

    def test_retrieve(self):
        instance = ListEmbeddingDoc.objects.create(
            embedded_list=[DumbEmbedded(name="Foo"), DumbEmbedded(name="Bar")]
        )

        serializer = ListEmbeddingSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded_list': [
                OrderedDict((('name', "Foo"), ('foo', None))),
                OrderedDict((('name', "Bar"), ('foo', None)))
            ],
        }
        assert serializer.data == expected

    def test_create(self):
        data = {
            'embedded_list': [
                {'name': "Foo"},
                {'foo': 123}
            ]
        }

        serializer = ListEmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance, ListEmbeddingDoc)
        assert isinstance(instance.embedded_list[0], DumbEmbedded)
        assert instance.embedded_list[0].name == "Foo"
        assert instance.embedded_list[0].foo is None
        assert instance.embedded_list[1].name is None
        assert instance.embedded_list[1].foo == 123

        expected = {
            'id': str(instance.id),
            'embedded_list': [
                OrderedDict((('name', "Foo"), ('foo', None))),
                OrderedDict((('name', None), ('foo', 123)))
            ]
        }
        assert serializer.data == expected

    def test_update(self):
        instance = ListEmbeddingDoc.objects.create(
            embedded_list=[DumbEmbedded(name="Foo"), DumbEmbedded(name="Bar")]
        )

        data = {
            'embedded_list': [
                OrderedDict((('name', "Baz"), ('foo', 321)))
            ]
        }
        import pdb
        pdb.set_trace()
        serializer = ListEmbeddingSerializer(instance, data=data)

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert isinstance(instance, ListEmbeddingDoc)
        assert isinstance(instance.embedded_list[0], DumbEmbedded)
        assert len(instance.embedded_list) == 1
        assert instance.embedded_list[0].name == "Baz"
        assert instance.embedded_list[0].foo == 321

        expected = {
            'id': str(instance.id),
            'embedded_list': [OrderedDict((('name', "Baz"), ('foo', 321)))],
        }
        assert serializer.data == expected

    @pytest.mark.skipif(True, reason="TODO")
    def test_update_partial(self):
        pass


class ValidatingEmbeddedModel(EmbeddedDocument):
    text = fields.StringField(min_length=3)


class ValidatingEmbeddingModel(Document):
    embedded = fields.EmbeddedDocumentField(ValidatingEmbeddedModel)


class ValidatingSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingEmbeddingModel
        depth = 1


class ValidatingListEmbeddingModel(Document):
    embedded_list = fields.EmbeddedDocumentListField(ValidatingEmbeddedModel)


class ValidatingListSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingListEmbeddingModel
        depth = 1


class TestEmbeddedValidation(TestCase):
    def test_validation_failing(self):
        serializer = ValidatingSerializer(data={'embedded': {'text': 'Fo'}})
        assert not serializer.is_valid()
        assert 'embedded' in serializer.errors
        assert 'text' in serializer.errors['embedded']

    def test_validation_passing(self):
        serializer = ValidatingSerializer(data={'embedded': {'text': 'Text'}})
        assert serializer.is_valid(), serializer.errors

    def test_nested_validation_failing(self):
        serializer = ValidatingListSerializer(data={'embedded_list': [{'text': 'Fo'}]})
        assert not serializer.is_valid()
        assert 'embedded_list' in serializer.errors
        assert 'text' in serializer.errors['embedded_list']

    def test_nested_validation_passing(self):
        serializer = ValidatingListSerializer(data={'embedded_list': [{'text': 'Text'}]})
        assert serializer.is_valid(), serializer.errors
