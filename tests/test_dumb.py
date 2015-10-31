from __future__ import unicode_literals

import pytest
from django.test import TestCase

from mongoengine import Document, fields

from rest_framework_mongoengine import serializers


class MockModel(Document):
    foo = fields.StringField()


class TestSomething(TestCase):
    def test_something(self):
        class TestSerializer(serializers.DocumentSerializer):
            class Meta:
                model = MockModel

        serializer = TestSerializer(data={'foo':"Foo"})
        self.assertTrue(serializer.is_valid())

    # def test_skipped(self):
    #     pytest.skip("just a sample")

    # def test_debugged(self):
    #     pytest.set_trace()
