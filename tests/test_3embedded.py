import pytest

from django.test import TestCase

from mongoengine import Document, EmbeddedDocument, fields

class EmbeddedModel(EmbeddedDocument):
    foo = fields.StringField()

class EmbeddingModel(Document):
    embedded_field = fields.EmbeddedDocumentField(EmbeddedModel)
    generic_embedded_field = fields.GenericEmbeddedDocumentField()

class TestMapping(TestCase):
    def test_mapping(self):
        pytest.skip("TODO")
