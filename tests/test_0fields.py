from __future__ import unicode_literals

import pytest

from bson import ObjectId

from django.test import TestCase

from rest_framework.exceptions import ValidationError

from mongoengine import Document, EmbeddedDocument, fields

from rest_framework_mongoengine.fields import (ObjectIdField, DocumentField, GenericField)

from .utils import FieldValues


class TestObjectId(FieldValues, TestCase):
    field = ObjectIdField()
    valid_inputs = {
        ObjectId('56353a4aa21aab2c49d86ebb'): ObjectId('56353a4aa21aab2c49d86ebb'),
        '56353a4aa21aab2c49d86ebb': ObjectId('56353a4aa21aab2c49d86ebb')
    }
    invalid_inputs = {
        123: ['123 is not a valid ObjectId'],
        'xxx': ['\'xxx\' is not a valid ObjectId']
    }
    outputs = {
        ObjectId('56353a4aa21aab2c49d86ebb'): '56353a4aa21aab2c49d86ebb',
        '56353a4aa21aab2c49d86ebb': '56353a4aa21aab2c49d86ebb'
    }


class MockModel(Document):
    foo = fields.IntField()


class TestDocumentField(TestCase):

    def tearDown(self):
        MockModel.drop_collection()

    field = DocumentField(model_field=MockModel.foo)

    def test_inputs(self):
        assert self.field.to_internal_value("123") == 123
        assert self.field.to_internal_value(123) == 123

    def test_errors(self):
        with pytest.raises(ValidationError):
            self.field.run_validation("xxx")

    def test_output(self):
        instance = MockModel.objects.create(foo=123)
        assert self.field.to_representation(instance) == 123


class MockEmbeddedModel(EmbeddedDocument):
    foo = fields.IntField()


class TestGenericField(FieldValues, TestCase):
    field = GenericField()

    valid_inputs = [
        ("str", "str"),
        (123, 123),
        ([1,2,3], [1,2,3]),
        ({'foo':"Foo"}, {'foo':"Foo"}),
        ({ '_cls': 'MockEmbeddedModel', 'foo': "Foo"}, MockEmbeddedModel(foo="Foo")),
        ({ 'emb': { '_cls': 'MockEmbeddedModel', 'foo': "Foo"}}, {'emb': MockEmbeddedModel(foo="Foo")}),
    ]

    invalid_inputs = [
        ({ '_cls': 'InvalidModel', 'foo': "Foo"}, ["`InvalidModel` has not been defined."]),
    ]

    outputs = [
        ("str", "str"),
        (123, 123),
        ([1,2,3], [1,2,3]),
        ({'foo':"Foo"}, {'foo':"Foo"}),
        (MockEmbeddedModel(foo="Foo"), { '_cls': 'MockEmbeddedModel', 'foo': "Foo"}),
        ({'emb': MockEmbeddedModel(foo="Foo")}, { 'emb': { '_cls': 'MockEmbeddedModel', 'foo': "Foo"}}),
    ]
