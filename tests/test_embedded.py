from collections import OrderedDict

import pytest
from django.test import TestCase
from mongoengine import Document, EmbeddedDocument, fields
from rest_framework import fields as drf_fields
from rest_framework.compat import unicode_repr
from rest_framework.serializers import Field, Serializer
from rest_framework_mongoengine.fields import (DocumentField,
                                               GenericEmbeddedField)
from rest_framework_mongoengine.serializers import (DocumentSerializer,
                                                    EmbeddedDocumentSerializer)

from .models import DumbEmbedded
from .utils import FieldTest, dedent


class OrderedEmbedded(EmbeddedDocument):
    f2 = fields.IntField()
    f0 = fields.IntField()
    f1 = fields.IntField()


class TestGenericEmbeddedField(FieldTest, TestCase):
    field = GenericEmbeddedField()

    valid_inputs = [
        ({'_cls': 'DumbEmbedded', 'name': "Name"}, DumbEmbedded(name="Name")),
    ]

    invalid_inputs = [
        ({'_cls': 'InvalidModel', 'name': "Name"}, "Document `InvalidModel` has not been defined."),
    ]

    outputs = [
        (DumbEmbedded(name="Name"), {'_cls': 'DumbEmbedded', 'name': "Name", 'foo': None}),
    ]


class NestedEmbeddedDoc(EmbeddedDocument):
    name = fields.StringField()
    embedded = fields.EmbeddedDocumentField(DumbEmbedded)


class SelfEmbeddingDoc(EmbeddedDocument):
    name = fields.StringField()
    embedded = fields.EmbeddedDocumentField('self')


class EmbeddingDoc(Document):
    embedded = fields.EmbeddedDocumentField(DumbEmbedded)


class OrderedEmbeddingDoc(Document):
    embedded = fields.EmbeddedDocumentField(OrderedEmbedded)


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
        class EmbeddingSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = DumbEmbedded
        expected = dedent("""
            EmbeddingSerializer():
                name = CharField(required=False)
                foo = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embbedded_order(self):
        class EmbeddingSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = OrderedEmbedded
        expected = dedent("""
            EmbeddingSerializer():
                f2 = IntegerField(required=False)
                f0 = IntegerField(required=False)
                f1 = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
                depth = 1
        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        foo = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_nodepth(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
                depth = 0
        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        foo = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_restricted(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
                depth_embedding = 1
        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = HiddenField(default=None, required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_recursive(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingDoc

        expected = dedent("""
            EmbeddingSerializer():
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

        serializer = EmbeddingSerializer()
        assert unicode_repr(serializer) == expected

    def test_embedding_recursive_restricted(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = RecursiveEmbeddingDoc
                depth_embedding = 2
        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        embedded = HiddenField(default=None, required=False)
        """)

        serializer = EmbeddingSerializer()
        assert unicode_repr(serializer) == expected

    def test_embedding_nested(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = NestedEmbeddingDoc
        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    embedded = EmbeddedSerializer(required=False):
                        name = CharField(required=False)
                        foo = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_list(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = ListEmbeddingDoc
        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded_list = EmbeddedSerializer(many=True, required=False):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_required(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = RequiredEmbeddingDoc
        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=True):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_generic(self):
        class EmbeddingSerializer(DocumentSerializer):
            class Meta:
                model = GenericEmbeddingDoc

        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = GenericEmbeddedDocumentField(model_field=<mongoengine.fields.GenericEmbeddedDocumentField: embedded>, required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_custom_generic(self):

        class CustomEmbedding(DocumentField):
            pass

        class EmbeddingSerializer(DocumentSerializer):
            serializer_embedded_generic = CustomEmbedding

            class Meta:
                model = GenericEmbeddingDoc

        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = CustomEmbedding(model_field=<mongoengine.fields.GenericEmbeddedDocumentField: embedded>, required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_custom_nested(self):
        class CustomEmbeddingSerializer(Serializer):
            bla = drf_fields.CharField()

        class EmbeddingSerializer(DocumentSerializer):
            serializer_embedded_nested = CustomEmbeddingSerializer

            class Meta:
                model = NestedEmbeddingDoc

        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = EmbeddedSerializer(required=False):
                    bla = CharField()
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected

    def test_embedding_custom_bottom(self):
        class CustomEmbedding(Field):
            bla = drf_fields.CharField()

        class EmbeddingSerializer(DocumentSerializer):
            serializer_embedded_bottom = CustomEmbedding

            class Meta:
                model = NestedEmbeddingDoc
                depth_embedding = 0

        expected = dedent("""
            EmbeddingSerializer():
                id = ObjectIdField(read_only=True)
                embedded = CustomEmbedding(default=None, required=False)
        """)
        assert unicode_repr(EmbeddingSerializer()) == expected


class EmbeddingSerializer(DocumentSerializer):
    class Meta:
        model = EmbeddingDoc


class NestedEmbeddingSerializer(DocumentSerializer):
    class Meta:
        model = NestedEmbeddingDoc


class TestEmbeddingIntegration(TestCase):
    def tearDown(self):
        EmbeddingDoc.drop_collection()

    def test_parse(self):
        data = {
            'embedded': {'name': "emb"}
        }

        serializer = EmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            'embedded': DumbEmbedded(name="emb")
        }
        assert serializer.validated_data == expected

    def test_ordering(self):
        class EmbeddingSerializer(EmbeddedDocumentSerializer):
            class Meta:
                model = OrderedEmbeddingDoc

        data = {
            'embedded': {'f0': 0, 'f1': 1, 'f2': 2}
        }

        serializer = EmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            'embedded': OrderedDict((('f2', 2), ('f0', 0), ('f1', 1)))
        }
        assert serializer.data == expected

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
        assert instance.embedded.name == "emb"

        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((('name', "emb"), ('foo', None))),
        }
        assert serializer.data == expected

    def test_update(self):
        " whole embedded is overwritten "
        instance = EmbeddingDoc.objects.create(
            embedded=DumbEmbedded(name="emb", foo=123)
        )

        data = {
            'embedded': {'foo': 321}
        }
        serializer = EmbeddingSerializer(instance, data=data)

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.embedded.name is None
        assert instance.embedded.foo == 321

        expected = {
            'id': str(instance.id),
            'embedded': OrderedDict((('name', None), ('foo', 321))),
        }
        assert serializer.data == expected


class GenericEmbeddingSerializer(DocumentSerializer):
    class Meta:
        model = GenericEmbeddingDoc


class TestGenericEmbeddingIntegration(TestCase):
    def tearDown(self):
        GenericEmbeddingDoc.drop_collection()

    def test_parse(self):
        data = {
            'embedded': {'_cls': 'DumbEmbedded', 'name': "emb"}
        }

        serializer = GenericEmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            'embedded': DumbEmbedded(name="emb")
        }
        assert serializer.validated_data == expected

    @pytest.mark.skipif(True, reason="TODO")
    def test_ordering(self):
        data = {
            'embedded': {'_cls': 'OrderedEmbedded', 'f0': 0, 'f1': 1, 'f2': 2}
        }

        serializer = GenericEmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        expected = {
            'embedded': OrderedDict((('_cls', 'OrderedEmbedded'), ('f2', 2), ('f0', 0), ('f1', 1)))
        }
        assert serializer.data == expected

    def test_retrieve(self):
        instance = GenericEmbeddingDoc.objects.create(
            embedded=DumbEmbedded(name="emb")
        )
        serializer = GenericEmbeddingSerializer(instance)
        expected = {
            'id': str(instance.id),
            'embedded': {'_cls': 'DumbEmbedded', 'name': "emb", 'foo': None},
        }
        # pass OrderedDict
        assert dict(serializer.data['embedded']) == expected['embedded']

    def test_create(self):
        data = {
            'embedded': {'_cls': 'DumbEmbedded', 'name': "emb"}
        }

        serializer = GenericEmbeddingSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.embedded == DumbEmbedded(name="emb")

        expected = {
            'id': str(instance.id),
            'embedded': {'_cls': 'DumbEmbedded', 'name': "emb", 'foo': None},
        }
        # pass OrderedDict
        assert dict(serializer.data['embedded']) == expected['embedded']

    def test_update(self):
        instance = GenericEmbeddingDoc.objects.create(
            embedded=DumbEmbedded(name="Dumb", foo=123)
        )

        data = {
            'embedded': {'_cls': 'DumbEmbedded', 'foo': 321}
        }
        serializer = GenericEmbeddingSerializer(instance, data=data)

        assert serializer.is_valid(), serializer.errors

        instance = serializer.save()
        assert instance.embedded.name is None
        assert instance.embedded.foo == 321

        expected = {
            'id': str(instance.id),
            'embedded': {'_cls': 'DumbEmbedded', 'name': None, 'foo': 321},
        }
        # pass OrderedDict
        assert dict(serializer.data['embedded']) == expected['embedded']


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
