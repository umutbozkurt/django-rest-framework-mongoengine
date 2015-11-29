from __future__ import unicode_literals

import pytest
import datetime
from django.test import TestCase

from mongoengine import Document, fields

from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine.validators import UniqueValidator, UniqueTogetherValidator

from .utils import dedent

class ValidatingModel(Document):
    name = fields.StringField()
    code = fields.IntField()

class NullValidatingModel(Document):
    name = fields.StringField()
    code = fields.IntField(null=True)
    other = fields.StringField(null=True)


# Tests for explicit `UniqueValidator`
# ------------------------------------

class UniqueValidatorSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingModel

    name = serializers.CharField(validators=[UniqueValidator(queryset=ValidatingModel.objects)])


class TestUniqueValidation(TestCase):
    def setUp(self):
        self.instance = ValidatingModel.objects.create(name='existing')

    def tearDown(self):
        ValidatingModel.drop_collection()

    def test_repr(self):
        serializer = UniqueValidatorSerializer()
        expected = dedent("""
            UniqueValidatorSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(validators=[<UniqueValidator(queryset=ValidatingModel.objects)>])
                code = IntegerField(required=False)
        """)
        assert repr(serializer) == expected

    def test_is_not_unique(self):
        data = {'name': 'existing'}
        serializer = UniqueValidatorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        assert serializer.errors == {'name': ['This field must be unique.']}

    def test_is_unique(self):
        data = {'name': 'other'}
        serializer = UniqueValidatorSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        assert serializer.validated_data == {'name': 'other'}

    def test_updated_instance_excluded(self):
        data = {'name': 'existing'}
        serializer = UniqueValidatorSerializer(self.instance, data=data)
        self.assertTrue(serializer.is_valid())
        assert serializer.validated_data == {'name': 'existing'}


# Tests for implicit `UniqueValidator`
# ------------------------------------



    # def test_doesnt_pollute_model(self):
    #     instance = AnotherUniquenessModel.objects.create(code='100')
    #     serializer = AnotherUniquenessSerializer(instance)
    #     self.assertEqual(
    #         AnotherUniquenessModel._meta.get_field('code').validators, [])

    #     # Accessing data shouldn't effect validators on the model
    #     serializer.data
    #     self.assertEqual(
    #         AnotherUniquenessModel._meta.get_field('code').validators, [])


# Tests for explicit `UniqueTogetherValidator`
# -----------------------------------
class UniqueTogetherValidatorSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingModel
        validators = [UniqueTogetherValidator(queryset=ValidatingModel.objects, fields=('name', 'code'))]

class NullUniqueValidatorSerializer(DocumentSerializer):
    class Meta:
        model = NullValidatingModel
        validators = [UniqueTogetherValidator(queryset=ValidatingModel.objects, fields=('name', 'code'))]

class TestUniqueTogetherValidation(TestCase):
    def setUp(self):
        self.instance = ValidatingModel.objects.create(
            name='example',
            code=1
        )
        ValidatingModel.objects.create(
            name='example',
            code=2
        )
        ValidatingModel.objects.create(
            name='other',
            code=1
        )
    def tearDown(self):
        ValidatingModel.drop_collection()
        NullValidatingModel.drop_collection()

    def test_repr(self):
        serializer = UniqueTogetherValidatorSerializer()
        expected = dedent("""
            UniqueTogetherValidatorSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
                code = IntegerField(required=False)
                class Meta:
                    validators = [<UniqueTogetherValidator(queryset=ValidatingModel.objects, fields=('name', 'code'))>]
        """)
        assert repr(serializer) == expected

    def test_is_not_unique_together(self):
        """
        Failing unique together validation should result in non field errors.
        """
        data = { 'name': 'example', 'code': 2}
        serializer = UniqueTogetherValidatorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        assert serializer.errors == {
            'non_field_errors': [
                'The fields name, code must make a unique set.'
            ]
        }

    def test_is_unique_together(self):
        """
        In a unique together validation, one field may be non-unique
        so long as the set as a whole is unique.
        """
        data = {'name': 'other', 'code': 2}
        serializer = UniqueTogetherValidatorSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        assert serializer.validated_data == {
            'name': 'other',
            'code': 2
        }

    def test_updated_instance_excluded_from_unique_together(self):
        """
        When performing an update, the existing instance does not count
        as a match against uniqueness.
        """
        data = {'name': 'example', 'code': 1}
        serializer = UniqueTogetherValidatorSerializer(self.instance, data=data)
        self.assertTrue(serializer.is_valid())
        assert serializer.validated_data == {
            'name': 'example',
            'code': 1
        }

    def test_unique_together_is_required(self):
        """
        In a unique together validation, all fields are required.
        """
        data = {'code': 2}
        serializer = UniqueTogetherValidatorSerializer(data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        assert serializer.errors == {
            'name': ['This field is required.']
        }

    # def test_ignore_excluded_fields(self):
    #     """
    #     When model fields are not included in a serializer, then uniqueness
    #     validators should not be added for that field.
    #     """
    #     class ExcludedFieldSerializer(serializers.ModelSerializer):
    #         class Meta:
    #             model = ValidatingModel
    #             fields = ('id', 'name',)
    #     serializer = ExcludedFieldSerializer()
    #     expected = dedent("""
    #         ExcludedFieldSerializer():
    #             id = IntegerField(label='ID', read_only=True)
    #             name = CharField(max_length=100)
    #     """)
    #     assert repr(serializer) == expected

    # def test_ignore_validation_for_null_fields(self):
    #     # None values that are on fields which are part of the uniqueness
    #     # constraint cause the instance to ignore uniqueness validation.
    #     NullValidatingModel.objects.create(
    #         other="xxx",
    #         name='existing',
    #         code=None
    #     )
    #     data = {
    #         'name': 'existing',
    #         'code': None,
    #         'other': "xxx",
    #     }
    #     serializer = NullUniqueValidatorSerializer(data=data)
    #     self.assertTrue(serializer.is_valid())

    # def test_do_not_ignore_validation_for_null_fields(self):
    #     # None values that are not on fields part of the uniqueness constraint
    #     # do not cause the instance to skip validation.
    #     NullValidatingModel.objects.create(
    #         other="xxx",
    #         name='existing',
    #         code=1
    #     )
    #     data = {'name': 'existing', 'code': 1}
    #     serializer = NullUniqueValidatorSerializer(data=data)
    #     self.assertFalse(serializer.is_valid())
