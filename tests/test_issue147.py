from __future__ import unicode_literals

from django.test import TestCase

from mongoengine import Document, EmbeddedDocument, fields
from rest_framework import fields as drf_fields

from rest_framework_mongoengine.serializers import DocumentSerializer, EmbeddedDocumentSerializer


class EmbeddedThing(EmbeddedDocument):
    test_field = fields.StringField(min_length=3)


class EmbeddingThing(Document):
    embedded = fields.EmbeddedDocumentListField(EmbeddedThing)


class EmbeddedThingSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = EmbeddedThing


class ExplicitSerializer(DocumentSerializer):
    class Meta:
        model = EmbeddingThing
        depth = 1
    embedded = drf_fields.ListField(child=EmbeddedThingSerializer())


class ExplicitManySerializer(DocumentSerializer):
    class Meta:
        model = EmbeddingThing
        depth = 1
    embedded = EmbeddedThingSerializer(many=True)


class ImplicitSerializer(DocumentSerializer):
    class Meta:
        model = EmbeddingThing
        depth = 1


class Issue147Test(TestCase):
    def test_explicit_pass(self):
        serializer = ExplicitSerializer(data={'embedded': [{'test_field': 'Test'}]})
        self.assertTrue(serializer.is_valid())

    def test_explicit_fail(self):
        serializer = ExplicitSerializer(data={'embedded': [{'test_field': 'Te'}]})
        self.assertFalse(serializer.is_valid())

    def test_explicitmany_pass(self):
        serializer = ExplicitManySerializer(data={'embedded': [{'test_field': 'Test'}]})
        self.assertTrue(serializer.is_valid())

    def test_explicitmany_fail(self):
        serializer = ExplicitManySerializer(data={'embedded': [{'test_field': 'Te'}]})
        self.assertFalse(serializer.is_valid())

    def test_implicit_pass(self):
        serializer = ImplicitSerializer(data={'embedded': [{'test_field': 'Test'}]})
        self.assertTrue(serializer.is_valid())

    def test_implicit_fail(self):
        serializer = ImplicitSerializer(data={'embedded': [{'test_field': 'Te'}]})
        self.assertFalse(serializer.is_valid())
