from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, fields
from rest_framework import serializers

from rest_framework_mongoengine.serializers import DocumentSerializer
from rest_framework_mongoengine.validators import (
    UniqueTogetherValidator, UniqueValidator
)

from .utils import dedent


class NonValidatingModel(Document):
    name = fields.StringField()
    code = fields.IntField()


class UniqueValidatingModel(Document):
    name = fields.StringField(unique=True)
    code = fields.IntField()


class NullValidatingModel(Document):
    name = fields.StringField()
    code = fields.IntField(null=True)
    other = fields.StringField(null=True)


# Tests for explicit `UniqueValidator`
# ------------------------------------

class UniqueValidatorSerializer(DocumentSerializer):
    class Meta:
        model = NonValidatingModel
        fields = '__all__'

    name = serializers.CharField(validators=[UniqueValidator(queryset=NonValidatingModel.objects)])


class TestUniqueValidation(TestCase):
    def setUp(self):
        self.instance = NonValidatingModel.objects.create(name='existing')

    def doCleanups(self):
        NonValidatingModel.drop_collection()

    def test_repr(self):
        serializer = UniqueValidatorSerializer()
        expected = dedent("""
            UniqueValidatorSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(validators=[<UniqueValidator(queryset=NonValidatingModel.objects)>])
                code = IntegerField(required=False)
        """)
        assert repr(serializer) == expected

    def test_is_not_unique(self):
        data = {'name': 'existing'}
        serializer = UniqueValidatorSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'name': ['This field must be unique.']}

    def test_is_unique(self):
        data = {'name': 'other'}
        serializer = UniqueValidatorSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {'name': 'other'}

    def test_updated_instance_excluded(self):
        data = {'name': 'existing'}
        serializer = UniqueValidatorSerializer(self.instance, data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == {'name': 'existing'}


# Tests for implicit `UniqueValidator`
# ------------------------------------


class TestUniqueSerializer(TestCase):
    def test_repr(self):
        class UniqueSerializer(DocumentSerializer):
            class Meta:
                model = UniqueValidatingModel
                fields = '__all__'

        serializer = UniqueSerializer()

        expected = dedent("""
            UniqueSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=True, validators=[<UniqueValidator(queryset=UniqueValidatingModel.objects)>])
                code = IntegerField(required=False)
        """)
        assert repr(serializer) == expected


# Tests for explicit `UniqueTogetherValidator`
# -----------------------------------
class UniqueTogetherValidatorSerializer(DocumentSerializer):
    class Meta:
        model = NonValidatingModel
        fields = '__all__'
        validators = [UniqueTogetherValidator(queryset=NonValidatingModel.objects, fields=('name', 'code'))]


class NullUniqueTogetherValidatorSerializer(DocumentSerializer):
    class Meta:
        model = NullValidatingModel
        fields = '__all__'
        validators = [UniqueTogetherValidator(queryset=NullValidatingModel.objects, fields=('name', 'code'))]


class TestUniqueTogetherValidation(TestCase):
    def setUp(self):
        self.instance = NonValidatingModel.objects.create(
            name='example',
            code=1
        )
        NonValidatingModel.objects.create(
            name='example',
            code=2
        )
        NonValidatingModel.objects.create(
            name='other',
            code=1
        )

    def doCleanups(self):
        NonValidatingModel.drop_collection()
        NullValidatingModel.drop_collection()

    def test_repr(self):
        serializer = UniqueTogetherValidatorSerializer()
        expected = dedent("""
            UniqueTogetherValidatorSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
                code = IntegerField(required=False)
                class Meta:
                    validators = [<UniqueTogetherValidator(queryset=NonValidatingModel.objects, fields=('name', 'code'))>]
        """)
        assert repr(serializer) == expected

    def test_repr_null(self):
        serializer = NullUniqueTogetherValidatorSerializer()
        expected = dedent("""
            NullUniqueTogetherValidatorSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
                code = IntegerField(allow_null=True, required=False)
                other = CharField(allow_blank=True, allow_null=True, required=False)
                class Meta:
                    validators = [<UniqueTogetherValidator(queryset=NullValidatingModel.objects, fields=('name', 'code'))>]
        """)
        assert repr(serializer) == expected

    def test_is_not_unique_together(self):
        """
        Failing unique together validation should result in non field errors.
        """
        data = {'name': 'example', 'code': 2}
        serializer = UniqueTogetherValidatorSerializer(data=data)
        assert not serializer.is_valid()
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
        assert serializer.is_valid(), serializer.errors
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
        assert serializer.is_valid(), serializer.errors
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
        assert not serializer.is_valid()
        assert serializer.errors == {
            'name': ['This field is required.']
        }

    def test_ignore_validation_for_null_fields(self):
        # None values that are on fields which are part of the uniqueness
        # constraint cause the instance to ignore uniqueness validation.
        NullValidatingModel.objects.create(
            name='existing',
            code=None,
            other="xxx"
        )

        class UniqueTogetherSerializer(DocumentSerializer):
            class Meta:
                model = NullValidatingModel
                fields = '__all__'
        data = {'name': 'existing', 'code': None, 'other': "xxx"}
        serializer = NullUniqueTogetherValidatorSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_do_not_ignore_validation_for_null_fields(self):
        # None values that are not on fields part of the uniqueness constraint
        # do not cause the instance to skip validation.
        NullValidatingModel.objects.create(
            name='existing',
            code=1,
            other="xxx"
        )
        data = {'name': 'existing', 'code': 1, 'other': None}
        serializer = NullUniqueTogetherValidatorSerializer(data=data)
        assert not serializer.is_valid()


# Tests for implicit `UniqueTogetherValidator`
# --------------------------------------------
class UniqueTogetherModel(Document):
    meta = {
        'indexes': [
            {'fields': ['name', 'code'], 'unique': True}
        ]
    }
    name = fields.StringField()
    code = fields.IntField()


class TestUniqueTogetherSerializer(TestCase):
    def doCleanups(self):
        NonValidatingModel.drop_collection()
        NullValidatingModel.drop_collection()

    def test_repr(self):
        class UniqueTogetherSerializer(DocumentSerializer):
            class Meta:
                model = UniqueTogetherModel
                fields = '__all__'

        serializer = UniqueTogetherSerializer()

        expected = dedent("""
            UniqueTogetherSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=True)
                code = IntegerField(required=True)
                class Meta:
                    validators = [<UniqueTogetherValidator(queryset=UniqueTogetherModel.objects, fields=('name', 'code'))>]
        """)
        assert repr(serializer) == expected

    def test_excluded_fields(self):
        """
        When model fields are not included in a serializer and have no defaults,
        then uniqueness validators should not be added for that field.
        """
        class UniqueTogetherSerializer(DocumentSerializer):
            class Meta:
                model = UniqueTogetherModel
                fields = ('id', 'name')

        serializer = UniqueTogetherSerializer()

        expected = dedent("""
            UniqueTogetherSerializer():
                id = ObjectIdField(read_only=True)
                name = CharField(required=False)
        """)
        assert repr(serializer) == expected
