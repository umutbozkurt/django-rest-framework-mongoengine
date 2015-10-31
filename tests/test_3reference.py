import pytest

from django.test import TestCase

from mongoengine import Document, fields

class ReferencedModel(Document):
    str_field = fields.StringField()

class ReferencingModel(Document):
    ref_field = fields.ReferenceField(ReferencedModel)
    dbref_field = fields.ReferenceField(ReferencedModel,dbref=True)
    cache_ref_field = fields.CachedReferenceField(ReferencedModel)
    gen_ref_field = fields.GenericReferenceField()

class TestFields(TestCase):
    def test_mapping(self):
        pytest.skip("TODO")

class TestMapping(TestCase):
    def test_mapping(self):
        pytest.skip("TODO")
