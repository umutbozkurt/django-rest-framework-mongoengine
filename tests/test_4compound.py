import pytest

from django.test import TestCase
from mongoengine import Document, fields

from rest_framework.compat import unicode_repr
from rest_framework_mongoengine.serializers import DocumentSerializer

from .test_1basic import dedent

class BasicCompoundFieldsModel(Document):
    """
    A model class for testing compound fields.
    """
    list_field = fields.ListField()
    int_list_field = fields.ListField(fields.IntField())
    dict_field = fields.DictField()
    int_dict_field = fields.DictField(field=fields.IntField())
    int_map_field = fields.MapField(fields.IntField())


class OptionsCompoundFieldsModel(Document):
    """
    A model class for testing compound fields.
    """
    int_list_field = fields.ListField(fields.IntField(min_value=3, max_value=7))


class TestCompundFieldMappings(TestCase):
    maxDiff = 10000

    def test_basic_fields(self):
        """
        Model fields should map to their equivelent serializer fields.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = BasicCompoundFieldsModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                list_field = ListField(required=False)
                int_list_field = ListField(child=IntegerField(required=False), required=False)
                dict_field = DictField(required=False)
                int_dict_field = DictField(child=IntegerField(required=False), required=False)
                int_map_field = DictField(child=IntegerField(required=False), required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_suboptions(self):
        """
        Model fields should map to their equivelent serializer fields.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = OptionsCompoundFieldsModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                int_list_field = ListField(child=IntegerField(max_value=7, min_value=3, required=False), required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)
