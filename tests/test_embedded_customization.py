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


class ParentDocument(Document):
    foo = fields.StringField()
    embedded = fields.EmbeddedDocumentField(ChildDocument)
    embedded_list = fields.EmbeddedDocumentListField(ChildDocument)
    embedded_map = fields.MapField(fields.EmbeddedDocumentField(ChildDocument))


class TestEmbeddedCustomizationMapping(TestCase):
    def test_fields(self):
        """
        Ensure `fields` is passed to embedded documents.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('embedded', 'embedded_list', 'embedded_map', 'embedded.name', 'embedded_list.name', 'embedded_map.name')

        # TODO: what if parent field is not included, but child field is?

    def test_exclude(self):
        """
        Ensure `exclude` is passed to embedded documents.
        """
        class ParentSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('__all__')
                exclude = ('foo', 'embedded.age', 'embedded_list.age', 'embedded_map.age')

        expected = dedent("""
            ParentSerializer():

        """)

    def test_read_only(self):
        """
        Ensure `read_only` are passed to embedded documents.
        """
        pass

    def test_extra_field_kwargs(self):
        """
        Ensure `extra_kwargs` are passed to embedded documents.
        """

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = ParentDocument
                fields = ('id', 'str_field')
                extra_kwargs = {'str_field': {'default': 'extra'}}

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                str_field = CharField(default='extra')
        """)
        assert unicode_repr(TestSerializer()) == expected


class TestEmbeddedCustomizationIntegration(TestCase):
    def test_exclude(self):
        pass

    def test_read_only(self):
        pass

    def test_extra_field_kwargs(self):
        pass
