from __future__ import unicode_literals

import pytest
from django.test import TestCase
from mongoengine import Document, EmbeddedDocument, fields
from rest_framework.fields import Field as BaseField
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class ReferencedModel(Document):
    name = fields.StringField()


class EmbeddedModel(EmbeddedDocument):
    name = fields.StringField()


class MockModel(Document):
    ref = fields.ReferenceField(ReferencedModel)
    genref = fields.GenericReferenceField()
    genemb = fields.GenericEmbeddedDocumentField()


class CustomRefField(BaseField):
    def __init__(self, model=None, queryset=None, **kwargs):
        super(CustomRefField, self).__init__(**kwargs)


class CustomGenRefField(BaseField):
    pass


class CustomGenEmbField(BaseField):
    def __init__(self, model_field=None, **kwargs):
        super(CustomGenEmbField, self).__init__(**kwargs)


class CustomSerializer(DocumentSerializer):
    serializer_reference_field = CustomRefField
    serializer_generic_reference_field = CustomGenRefField
    serializer_generic_embedded_field = CustomGenEmbField


class TestMapping(TestCase):
    def test_mapping_deep(self):
        class TestSerializer(CustomSerializer):
            class Meta:
                model = MockModel
                depth = 1

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    name = CharField(required=False)
                genref = CustomGenRefField(required=False)
                genemb = CustomGenEmbField(model_field=<mongoengine.fields.GenericEmbeddedDocumentField: genemb>, required=False)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_mapping_shallow(self):
        class TestSerializer(CustomSerializer):
            class Meta:
                model = MockModel
                depth = 0

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                ref = CustomRefField(queryset=ReferencedModel.objects)
                genref = CustomGenRefField(required=False)
                genemb = HiddenField(default=None)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)
