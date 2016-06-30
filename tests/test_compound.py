""" testing compound fields list and dict """
from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent


class BasicCompoundDoc(Document):
    list_field = fields.ListField()
    int_list_field = fields.ListField(fields.IntField())
    dict_field = fields.DictField()
    int_dict_field = fields.DictField(field=fields.IntField())
    int_map_field = fields.MapField(fields.IntField())


class OptionsCompoundDoc(Document):
    int_list_field = fields.ListField(fields.IntField(min_value=3, max_value=7))


class NestedCompoundDoc(Document):
    dict_list_field = fields.ListField(fields.DictField())
    list_dict_field = fields.MapField(fields.ListField())
    list_dict_list_field = fields.ListField(fields.MapField(fields.ListField()))


class TestCompundFieldMappings(TestCase):
    maxDiff = 10000

    def test_basic(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = BasicCompoundDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                list_field = ListField(required=False)
                int_list_field = ListField(child=IntegerField(required=False), required=False)
                dict_field = DictField(required=False)
                int_dict_field = DictField(child=IntegerField(required=False), required=False)
                int_map_field = DictField(child=IntegerField(required=False), required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_suboptions(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = OptionsCompoundDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                int_list_field = ListField(child=IntegerField(max_value=7, min_value=3, required=False), required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected

    def test_nested(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedCompoundDoc

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                dict_list_field = ListField(child=DictField(required=False), required=False)
                list_dict_field = DictField(child=ListField(required=False), required=False)
                list_dict_list_field = ListField(child=DictField(child=ListField(required=False), required=False), required=False)
        """)
        assert unicode_repr(TestSerializer()) == expected


class TestSerializer(DocumentSerializer):
    class Meta:
        model = BasicCompoundDoc


class TestIntegration(TestCase):
    def tearDown(self):
        BasicCompoundDoc.drop_collection()

    def test_parsing(self):
        input_data = {
            'list_field': ["1", 2, 3.0],
            'int_list_field': [1, 2, 3],
            'dict_field': {'a': "1", 'b': 2, 'c': 3.0},
            'int_dict_field': {'a': 1, 'b': 2, 'c': 3},
            'int_map_field': {'a': 1, 'b': 2, 'c': 3}
        }
        serializer = TestSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors
        expected = {
            'list_field': ["1", 2, 3.0],
            'int_list_field': [1, 2, 3],
            'dict_field': {'a': "1", 'b': 2, 'c': 3.0},
            'int_dict_field': {'a': 1, 'b': 2, 'c': 3},
            'int_map_field': {'a': 1, 'b': 2, 'c': 3}
        }
        assert serializer.validated_data == expected

    def test_retrival(self):
        instance = BasicCompoundDoc.objects.create(
            list_field=["1", 2, 3.0],
            int_list_field=[1, 2, 3],
            dict_field={'a': "1", 'b': 2, 'c': 3.0},
            int_dict_field={'a': 1, 'b': 2, 'c': 3},
            int_map_field={'a': 1, 'b': 2, 'c': 3}
        )
        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'list_field': ["1", 2, 3.0],
            'int_list_field': [1, 2, 3],
            'dict_field': {'a': "1", 'b': 2, 'c': 3.0},
            'int_dict_field': {'a': 1, 'b': 2, 'c': 3},
            'int_map_field': {'a': 1, 'b': 2, 'c': 3}
        }
        assert serializer.data == expected

    def test_create(self):
        data = {
            'list_field': ["1", 2, 3.0],
            'int_list_field': [1, 2, 3],
            'dict_field': {'a': "1", 'b': 2, 'c': 3.0},
            'int_dict_field': {'a': 1, 'b': 2, 'c': 3},
            'int_map_field': {'a': 1, 'b': 2, 'c': 3}
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.list_field == ["1", 2, 3.0]
        assert instance.int_list_field == [1, 2, 3]
        assert instance.dict_field == {'a': "1", 'b': 2, 'c': 3.0}
        assert instance.int_dict_field == {'a': 1, 'b': 2, 'c': 3}
        assert instance.int_map_field == {'a': 1, 'b': 2, 'c': 3}
        expected = {
            'id': str(instance.id),
            'list_field': ["1", 2, 3.0],
            'int_list_field': [1, 2, 3],
            'dict_field': {'a': "1", 'b': 2, 'c': 3.0},
            'int_dict_field': {'a': 1, 'b': 2, 'c': 3},
            'int_map_field': {'a': 1, 'b': 2, 'c': 3}
        }
        assert serializer.data == expected

    def test_update(self):
        instance = BasicCompoundDoc.objects.create(
            list_field=["1", 2, 3.0],
            int_list_field=[1, 2, 3],
            dict_field={'a': "1", 'b': 2, 'c': 3.0},
            int_dict_field={'a': 1, 'b': 2, 'c': 3},
            int_map_field={'a': 1, 'b': 2, 'c': 3}
        )
        data = {
            'list_field': ["0", 1, 2.0],
            'int_list_field': [9, 1, 2],
            'dict_field': {'a': "0", 'b': 1, 'c': 2.0, 'd': 3},
            'int_dict_field': {'a': 0, 'b': 1, 'c': 2, 'd': 3},
            'int_map_field': {'a': 0, 'b': 1, 'c': 2, 'd': 3}
        }
        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.list_field == ["0", 1, 2.0]
        assert instance.int_list_field == [9, 1, 2]
        assert instance.dict_field == {'a': "0", 'b': 1, 'c': 2.0, 'd': 3}
        assert instance.int_dict_field == {'a': 0, 'b': 1, 'c': 2, 'd': 3}
        assert instance.int_map_field == {'a': 0, 'b': 1, 'c': 2, 'd': 3}
        expected = {
            'id': str(instance.id),
            'list_field': ["0", 1, 2.0],
            'int_list_field': [9, 1, 2],
            'dict_field': {'a': "0", 'b': 1, 'c': 2.0, 'd': 3},
            'int_dict_field': {'a': 0, 'b': 1, 'c': 2, 'd': 3},
            'int_map_field': {'a': 0, 'b': 1, 'c': 2, 'd': 3}
        }
        assert serializer.data == expected


class ValidatingSerializer(DocumentSerializer):
    class Meta:
        model = OptionsCompoundDoc


class TestCompoundValidation(TestCase):
    def test_validation_is_executed(self):
        serializer = ValidatingSerializer(data={'int_list_field': [1, 2, 3]})
        assert not serializer.is_valid()
        assert 'int_list_field' in serializer.errors

    def test_validation_passing(self):
        serializer = ValidatingSerializer(data={'int_list_field': [3, 4, 5]})
        assert serializer.is_valid(), serializer.errors


# Check that Compound fields work with DocumentField
# So far implemented only for ListField, cause it's failing

class CompoundsWithDocumentFieldDoc(Document):
    list_field = fields.ListField(fields.DynamicField(null=True))


class CompoundsWithDocumentFieldSerializer(DocumentSerializer):
    class Meta:
        model = CompoundsWithDocumentFieldDoc


class TestCompoundsWithDocumentField(TestCase):
    def doCleanups(self):
        CompoundsWithDocumentFieldDoc.drop_collection()

    def test_parsing(self):
        input_data = {
            'list_field': [None, "1", 2, 3.0]
        }
        serializer = CompoundsWithDocumentFieldSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors
        expected = {
            'list_field': [None, "1", 2, 3.0]
        }
        assert serializer.validated_data == expected

    def test_retrieval(self):
        instance = CompoundsWithDocumentFieldDoc.objects.create(
            list_field=[None, "1", 2, 3.0]
        )
        serializer = CompoundsWithDocumentFieldSerializer(instance)
        expected = {
            'id': str(instance.id),
            'list_field': [None, "1", 2, 3.0]
        }
        assert serializer.data == expected

    def test_create(self):
        data = {
            'list_field': [None, "1", 2, 3.0]
        }

        serializer = CompoundsWithDocumentFieldSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.list_field == [None, "1", 2, 3.0]
        expected = {
            'id': str(instance.id),
            'list_field': [None, "1", 2, 3.0],
        }
        assert serializer.data == expected

    def test_update(self):
        instance = BasicCompoundDoc.objects.create(
            list_field=[None, "1", 2, 3.0]
        )
        data = {
            'list_field': ["0", 1, 2.0, None]
        }
        serializer = CompoundsWithDocumentFieldSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.list_field == ["0", 1, 2.0, None]
        expected = {
            'id': str(instance.id),
            'list_field': ["0", 1, 2.0, None]
        }
        assert serializer.data == expected
