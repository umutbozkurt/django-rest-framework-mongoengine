""" test for some general fields """

from __future__ import unicode_literals

import pytest
from bson import ObjectId
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from rest_framework_mongoengine.fields import (DocumentField, GenericField, ObjectIdField)

from .utils import FieldTest
from .models import DumbDocument, DumbEmbedded


class TestObjectId(FieldTest, TestCase):
    field = ObjectIdField()

    valid_inputs = {
        ObjectId('56353a4aa21aab2c49d86ebb'): ObjectId('56353a4aa21aab2c49d86ebb'),
        '56353a4aa21aab2c49d86ebb': ObjectId('56353a4aa21aab2c49d86ebb')
    }
    invalid_inputs = {
        123: "not a valid ObjectId",
        'xxx': "is not a valid ObjectId"
    }
    outputs = {
        ObjectId('56353a4aa21aab2c49d86ebb'): '56353a4aa21aab2c49d86ebb',
        '56353a4aa21aab2c49d86ebb': '56353a4aa21aab2c49d86ebb'
    }


class TestDocumentField(TestCase):

    def tearDown(self):
        DumbDocument.drop_collection()

    field = DocumentField(model_field=DumbDocument.foo)

    def test_inputs(self):
        assert self.field.to_internal_value("123") == 123
        assert self.field.to_internal_value(123) == 123

    def test_errors(self):
        with pytest.raises(ValidationError):
            self.field.run_validation("xxx")

    def test_output(self):
        instance = DumbDocument.objects.create(foo=123)
        assert self.field.to_representation(instance) == 123


class TestGenericField(FieldTest, TestCase):
    field = GenericField()

    valid_inputs = [
        ("str", "str"),
        (123, 123),
        ([1, 2, 3], [1, 2, 3]),
        ({'foo': "Foo"}, {'foo': "Foo"}),
        ({'_cls': 'DumbEmbedded', 'foo': "Foo"}, DumbEmbedded(foo="Foo")),
        ({'emb': {'_cls': 'DumbEmbedded', 'foo': "Foo"}}, {'emb': DumbEmbedded(foo="Foo")}),
    ]

    invalid_inputs = [
        ({'_cls': 'InvalidModel', 'foo': "Foo"}, "Document `InvalidModel` has not been defined."),
        ({'emb': {'_cls': 'InvalidModel', 'foo': "Foo"}}, "Document `InvalidModel` has not been defined."),
    ]

    outputs = [
        ("str", "str"),
        (123, 123),
        ([1, 2, 3], [1, 2, 3]),
        ({'foo': "Foo"}, {'foo': "Foo"}),
        (DumbEmbedded(foo="Foo"), {'_cls': 'DumbEmbedded', 'foo': "Foo", 'name': None}),
        ({'emb': DumbEmbedded(foo="Foo")}, {'emb': {'_cls': 'DumbEmbedded', 'foo': "Foo", 'name': None}}),
    ]
