"""
We want to allow users override fields and their attributes on
auto-generated embedded documents based on

We need to take into account the following fields:
 - exclude
 - read_only
 - extra_kwargs
"""

from __future__ import unicode_literals

import pytest
import six
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from mongoengine import Document, EmbeddedDocument, fields
from rest_framework import serializers
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class ChildDocument(EmbeddedDocument):
    name = fields.StringField()
    age = fields.IntField()


class ReferencedDocument(Document):
    foo = fields.StringField()


class ParentDocument(Document):
    foo = fields.StringField()
    embedded = fields.EmbeddedDocumentField(ChildDocument)
    embedded_list = fields.EmbeddedDocumentListField(ChildDocument)
    embedded_map = fields.MapField(fields.EmbeddedDocumentField(ChildDocument))
    nested_reference = fields.ReferenceField(ReferencedDocument)


class TestEmbeddedCustomizationMapping(TestCase):
    def test_fields(self):
        """
        Ensure `fields` is passed to embedded documents.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('embedded', 'embedded_list', 'embedded_map', 'embedded.name', 'embedded_list.name', 'embedded_map.name')

        expected = dedent("""
            ParentSerializer():
                foo = CharField()
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    age = IntegerField(required=False)
                embedded_list = ListSerializer(EmbeddedSerializer(required=False)):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
                embedded_map = DictField(EmbeddedSerializer(required=False)):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
                nested_reference = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    foo = CharField(required=False)
        """)
        # TODO: what if parent field is not included, but child field is?
        assert unicode_repr(ParentSerializer()) == expected

    def test_exclude(self):
        """
        Ensure `exclude` is passed to embedded documents.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                exclude = ('foo', 'embedded.age', 'embedded_list.age', 'embedded_map.age')

        expected = dedent("""
            ParentSerializer():
                foo = CharField()
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                embedded_list = ListSerializer(EmbeddedSerializer(required=False)):
                    name = CharField(required=False)
                    age = IntegerField(required=False)
                embedded_map = DictField(EmbeddedSerializer(required=False)):
                    name = CharField(required=False)
                    age = IntegerField(required=False)
                nested_reference = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    foo = CharField(required=False)
        """)

        assert unicode_repr(ParentSerializer()) == expected

    def test_read_only(self):
        """
        Ensure `read_only` are passed to embedded documents.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                read_only = ('foo', 'embedded.name', 'embedded_list.name', 'embedded_map.name')

        expected = dedent("""
            ParentSerializer():
                id = ObjectIdField(read_only=True)
                foo = CharField(required=False)
                embedded = EmbeddedSerializer(required=False):
                    name = CharField(required=False)
                    age = IntegerField(required=False)
                embedded_list = EmbeddedSerializer(many=True, required=False):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
                embedded_map = DictField(EmbeddedSerializer(required=False)):
                    name = CharField(required=False)
                    foo = IntegerField(required=False)
                nested_reference = NestedSerializer(read_only=True):
                    id = ObjectIdField(read_only=True)
                    foo = CharField(required=False)
        """)

        assert unicode_repr(ParentSerializer()) == expected


    def test_extra_field_kwargs(self):
        """
        Ensure `extra_kwargs` are passed to embedded documents.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                extra_kwargs = {
                    'foo': {'default': 'bar'},
                    'embedded.name': {'default': 'Johnny'},
                    'embedded_list.name': {'default': 'B.'},
                    'embedded_map.name': {'default': 'Good'}
                }

        expected = dedent("""
            ParentSerializer():
                foo = StringField(default='bar')
                str_field = CharField(default='extra')
        """)

        assert unicode_repr(DocumentSerializer()) == expected


class TestEmbeddedCustomizationIntegration(TestCase):
    def test_fields(self):
        pass

    def test_exclude(self):
        pass

    def test_read_only(self):
        pass

    def test_extra_field_kwargs(self):
        pass
