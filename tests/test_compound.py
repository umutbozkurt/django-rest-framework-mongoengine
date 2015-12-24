from django.test import TestCase
from mongoengine import Document, fields
from rest_framework.compat import unicode_repr

from rest_framework_mongoengine.serializers import DocumentSerializer

from .test_1basic import dedent


class BasicCompoundFieldsModel(Document):
    list_field = fields.ListField()
    int_list_field = fields.ListField(fields.IntField())
    dict_field = fields.DictField()
    int_dict_field = fields.DictField(field=fields.IntField())
    int_map_field = fields.MapField(fields.IntField())


class OptionsCompoundFieldsModel(Document):
    int_list_field = fields.ListField(fields.IntField(min_value=3, max_value=7))


class NestedCompoundFieldsModel(Document):
    dict_list_field = fields.ListField(fields.DictField())
    list_dict_field = fields.MapField(fields.ListField())
    list_dict_list_field = fields.ListField(fields.MapField(fields.ListField()))


class TestCompundFieldMappings(TestCase):
    maxDiff = 10000

    def test_basic(self):
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
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = OptionsCompoundFieldsModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                int_list_field = ListField(child=IntegerField(max_value=7, min_value=3, required=False), required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_nested(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = NestedCompoundFieldsModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                dict_list_field = ListField(child=DictField(required=False), required=False)
                list_dict_field = DictField(child=ListField(required=False), required=False)
                list_dict_list_field = ListField(child=DictField(child=ListField(required=False), required=False), required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)


class TestIntegration(TestCase):
    def tearDown(self):
        BasicCompoundFieldsModel.drop_collection()

    def test_retrival(self):
        instance = BasicCompoundFieldsModel.objects.create(
            list_field=["1", 2, 3.0],
            int_list_field=[1, 2, 3],
            dict_field={'a': "1", 'b': 2, 'c': 3.0},
            int_dict_field={'a': 1, 'b': 2, 'c': 3},
            int_map_field={'a': 1, 'b': 2, 'c': 3}
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = BasicCompoundFieldsModel

        serializer = TestSerializer(instance)
        expected = {
            'id': str(instance.id),
            'list_field': ["1", 2, 3.0],
            'int_list_field': [1, 2, 3],
            'dict_field': {'a': "1", 'b': 2, 'c': 3.0},
            'int_dict_field': {'a': 1, 'b': 2, 'c': 3},
            'int_map_field': {'a': 1, 'b': 2, 'c': 3}
        }
        self.assertEqual(serializer.data, expected)

    def test_create(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = BasicCompoundFieldsModel

        data = {
            'list_field': ["1", 2, 3.0],
            'int_list_field': [1, 2, 3],
            'dict_field': {'a': "1", 'b': 2, 'c': 3.0},
            'int_dict_field': {'a': 1, 'b': 2, 'c': 3},
            'int_map_field': {'a': 1, 'b': 2, 'c': 3}
        }

        serializer = TestSerializer(data=data)
        assert serializer.is_valid()

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
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        instance = BasicCompoundFieldsModel.objects.create(
            list_field=["1", 2, 3.0],
            int_list_field=[1, 2, 3],
            dict_field={'a': "1", 'b': 2, 'c': 3.0},
            int_dict_field={'a': 1, 'b': 2, 'c': 3},
            int_map_field={'a': 1, 'b': 2, 'c': 3}
        )

        class TestSerializer(DocumentSerializer):
            class Meta:
                model = BasicCompoundFieldsModel

        data = {
            'list_field': ["0", 1, 2.0],
            'int_list_field': [9, 1, 2],
            'dict_field': {'a': "0", 'b': 1, 'c': 2.0, 'd': 3},
            'int_dict_field': {'a': 0, 'b': 1, 'c': 2, 'd': 3},
            'int_map_field': {'a': 0, 'b': 1, 'c': 2, 'd': 3}
        }

        serializer = TestSerializer(instance, data=data)
        assert serializer.is_valid()

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
        self.assertEqual(serializer.data, expected)


class ValidatingSerializer(DocumentSerializer):
    class Meta:
        model = OptionsCompoundFieldsModel


class TestCompoundValidation(TestCase):
    def test_validation_is_executed(self):
        serializer = ValidatingSerializer(data={'int_list_field': [1, 2, 3]})
        self.assertFalse(serializer.is_valid())
        self.assertIn('int_list_field', serializer.errors)

    def test_validation_passing(self):
        serializer = ValidatingSerializer(data={'int_list_field': [3, 4, 5]})
        self.assertTrue(serializer.is_valid())
