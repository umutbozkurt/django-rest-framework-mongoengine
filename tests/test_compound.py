""" testing compound fields list and dict """
from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .models import DumbEmbedded
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
                fields = '__all__'

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
                fields = '__all__'

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
                fields = '__all__'

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
        fields = '__all__'


class TestIntegration(TestCase):
    def doCleanups(self):
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

    def test_retrieval(self):
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
        fields = '__all__'


class TestCompoundValidation(TestCase):
    def test_validation_is_executed(self):
        serializer = ValidatingSerializer(data={'int_list_field': [1, 2, 3]})
        assert not serializer.is_valid()
        assert 'int_list_field' in serializer.errors

    def test_validation_passing(self):
        serializer = ValidatingSerializer(data={'int_list_field': [3, 4, 5]})
        assert serializer.is_valid(), serializer.errors


# Mongoengine's ListField has a specific meaning of required argument
# Thus, we have to test that it's compatible with DRF's ListField

class RequiredListDocument(Document):
    required_list = fields.ListField(fields.StringField(), required=True)


class RequiredListSerializer(DocumentSerializer):
    class Meta:
        model = RequiredListDocument
        fields = '__all__'


class TestRequriedList(TestCase):
    def doCleanups(self):
        RequiredListDocument.drop_collection()

    def test_parsing(self):
        input_data = {
            'required_list': []
        }
        serializer = RequiredListSerializer(data=input_data)
        serializer.is_valid()
        assert serializer.errors['required_list'] == [u'This list may not be empty.']


# Check that ListField is allowed to be empty, if required=False

class NonRequiredListDocument(Document):
    non_required_list = fields.ListField(fields.StringField(), required=False)


class NonRequiredListSerializer(DocumentSerializer):
    class Meta:
        model = NonRequiredListDocument
        fields = '__all__'


class TestNonRequiredList(TestCase):
    def doCleanups(self):
        NonRequiredListDocument.drop_collection()

    def test_parsing(self):
        input_data = {
            'non_required_list': []
        }
        serializer = NonRequiredListSerializer(data=input_data)
        assert serializer.is_valid()


# Check that Compound fields work with DynamicField
# So far implemented only for ListField, cause it's failing

class CompoundsWithDynamicFieldDoc(Document):
    list_field = fields.ListField(fields.DynamicField(null=True))


class CompoundsWithDynamicFieldSerializer(DocumentSerializer):
    class Meta:
        model = CompoundsWithDynamicFieldDoc
        fields = '__all__'


class TestCompoundsWithDynamicField(TestCase):
    def doCleanups(self):
        CompoundsWithDynamicFieldDoc.drop_collection()

    def test_parsing(self):
        input_data = {
            'list_field': [None, "1", 2, 3.0]
        }
        serializer = CompoundsWithDynamicFieldSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors
        expected = {
            'list_field': [None, "1", 2, 3.0]
        }
        assert serializer.validated_data == expected

    def test_retrieval(self):
        instance = CompoundsWithDynamicFieldDoc.objects.create(
            list_field=[None, "1", 2, 3.0]
        )
        serializer = CompoundsWithDynamicFieldSerializer(instance)
        expected = {
            'id': str(instance.id),
            'list_field': [None, "1", 2, 3.0]
        }
        assert serializer.data == expected

    def test_create(self):
        data = {
            'list_field': [None, "1", 2, 3.0]
        }

        serializer = CompoundsWithDynamicFieldSerializer(data=data)
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
        serializer = CompoundsWithDynamicFieldSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.list_field == ["0", 1, 2.0, None]
        expected = {
            'id': str(instance.id),
            'list_field': ["0", 1, 2.0, None]
        }
        assert serializer.data == expected


class MapEmbeddedDoc(Document):
    embedded_map_field = fields.MapField(fields.EmbeddedDocumentField(DumbEmbedded))


class MapEmbeddedFieldSerializer(DocumentSerializer):
    class Meta:
        model = MapEmbeddedDoc
        fields = '__all__'


class TestMapFieldWithEmbeddedDocument(TestCase):
    def doCleanups(self):
        MapEmbeddedDoc.drop_collection()

    def test_parsing(self):
        input_data = {
            "embedded_map_field": {"a": {"name": "spam", "foo": 1}, "b": {"name": "ham", "foo": 2}},
        }
        serializer = MapEmbeddedFieldSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors
        expected = {
            "embedded_map_field": {"a": {"name": "spam", "foo": 1}, "b": {"name": "ham", "foo": 2}},
        }
        assert serializer.validated_data == expected

    def test_retrieval(self):
        instance = MapEmbeddedDoc.objects.create(
            embedded_map_field={"a": DumbEmbedded(name="spam", foo=1), "b": DumbEmbedded(name="ham", foo=2)},
        )
        serializer = MapEmbeddedFieldSerializer(instance)
        expected = {
            "id": str(instance.id),
            "embedded_map_field": {"a": {"name": "spam", "foo": 1}, "b": {"name": "ham", "foo": 2}},
        }
        assert serializer.data == expected

    def test_create(self):
        data = {
            "embedded_map_field": {"a": {"name": "spam", "foo": 1}, "b": {"name": "ham", "foo": 2}},
        }

        serializer = MapEmbeddedFieldSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        expected = {
            "id": str(instance.id),
            "embedded_map_field": {"a": {"name": "spam", "foo": 1}, "b": {"name": "ham", "foo": 2}},
        }
        assert serializer.data == expected

    def test_update(self):
        instance = MapEmbeddedDoc.objects.create(
            embedded_map_field={"a": DumbEmbedded(name="spam", foo=1), "b": DumbEmbedded(name="ham", foo=2)},
        )
        data = {
            "embedded_map_field": {"a": {"name": "spam", "foo": 3}, "b": {"name": "ham", "foo": 4}},
        }
        serializer = MapEmbeddedFieldSerializer(instance, data=data)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        expected = {
            "id": str(instance.id),
            "embedded_map_field": {"a": {"name": "spam", "foo": 3}, "b": {"name": "ham", "foo": 4}},
        }
        assert serializer.data == expected
