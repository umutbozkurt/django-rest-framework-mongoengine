"""
The `ModelSerializer` and `HyperlinkedModelSerializer` classes are essentially
shortcuts for automatically creating serializers based on a given model class.

These tests deal with ensuring that we correctly map the model fields onto
an appropriate set of serializer fields for each case.
"""
from __future__ import unicode_literals

import decimal
import pytest

from django.core.exceptions import ImproperlyConfigured

from mongoengine import Document, fields
from django.test import TestCase

from rest_framework.compat import unicode_repr
from rest_framework import serializers

from rest_framework_mongoengine.serializers import DocumentSerializer

from .utils import dedent

# Tests for regular field mappings.
# ---------------------------------

class CustomField(fields.BaseField):
    """
    A custom model field simply for testing purposes.
    """
    pass


class OneFieldModel(Document):
    str_field = fields.StringField()


class AutoFieldModel(Document):
    auto_field = fields.SequenceField(primary_key=True)


class RegularFieldsModel(Document):
    """
    A model class for testing regular flat fields.
    """
    str_field = fields.StringField()
    url_field = fields.URLField()
    email_field = fields.EmailField()
    int_field = fields.IntField()
    long_field = fields.LongField()
    float_field = fields.FloatField()
    boolean_field = fields.BooleanField()
    nullboolean_field = fields.BooleanField(null=True)
    date_field = fields.DateTimeField()
    complexdate_field = fields.ComplexDateTimeField()
    uuid_field = fields.UUIDField()
    id_field = fields.ObjectIdField()
    seq_field = fields.SequenceField()
    decimal_field = fields.DecimalField()

    # TODO
    # dynamic_field = fields.DynamicField()
    # bin_field = fields.BinaryField()
    # file_field = fields.FileField()
    # image_field = fields.ImageField()

    def method(self):
        return 'method'


COLOR_CHOICES = (('red', 'Red'), ('blue', 'Blue'), ('green', 'Green'))
DECIMAL_CHOICES = (('low', decimal.Decimal('0.1')), ('medium', decimal.Decimal('0.5')), ('high', decimal.Decimal('0.9')))


class FieldOptionsModel(Document):
    required_field = fields.IntField(required=True)
    null_field = fields.IntField(null=True)
    choices_field = fields.StringField(choices=COLOR_CHOICES)
    length_limit_field = fields.StringField(min_length=3, max_length=12)
    value_limit_field = fields.IntField(min_value=3, max_value=12)
    decimal_field = fields.DecimalField(precision=4, max_value=9999)

class ChoicesModel(Document):
    choices_field_with_nonstandard_args = fields.DecimalField(precision=1, choices=DECIMAL_CHOICES, verbose_name='A label')



class TestRegularFieldMappings(TestCase):
    maxDiff = 10000

    def test_regular_fields(self):
        """
        Model fields should map to their equivelent serializer fields.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularFieldsModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                str_field = CharField(required=False)
                url_field = URLField(required=False)
                email_field = EmailField(required=False)
                int_field = IntegerField(required=False)
                long_field = IntegerField(required=False)
                float_field = FloatField(required=False)
                boolean_field = BooleanField(required=False)
                nullboolean_field = NullBooleanField(required=False)
                date_field = DateTimeField(required=False)
                complexdate_field = DateTimeField(required=False)
                uuid_field = UUIDField(required=False)
                id_field = ObjectIdField(required=False)
                seq_field = IntegerField(read_only=True)
                decimal_field = DecimalField(decimal_places=2, max_digits=65536, required=False)
        """)

        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_field_options(self):
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = FieldOptionsModel

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                required_field = IntegerField(required=True)
                null_field = IntegerField(allow_null=True, required=False)
                choices_field = ChoiceField(choices=(('red', 'Red'), ('blue', 'Blue'), ('green', 'Green')), required=False)
                length_limit_field = CharField(max_length=12, min_length=3, required=False)
                value_limit_field = IntegerField(max_value=12, min_value=3, required=False)
                decimal_field = DecimalField(decimal_places=4, max_digits=8, max_value=9999, required=False)
        """)
        self.assertEqual(unicode_repr(TestSerializer()), expected)

    def test_method_field(self):
        """
        Properties and methods on the model should be allowed as `Meta.fields`
        values, and should map to `ReadOnlyField`.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('id', 'method')

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                method = ReadOnlyField()
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_pk_fields(self):
        """
        Both `pk` and the actual primary key name are valid in `Meta.fields`.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = AutoFieldModel
                fields = ('pk', 'auto_field')

        expected = dedent("""
            TestSerializer():
                pk = IntegerField(read_only=True)
                auto_field = IntegerField(read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_id_field(self):
        """
        The autocreated id field should be mapped properly
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = OneFieldModel
                fields = ('id',)

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
        """)
        self.assertEqual(repr(TestSerializer()), expected)

    def test_extra_field_kwargs(self):
        """
        Ensure `extra_kwargs` are passed to generated fields.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('id', 'str_field')
                extra_kwargs = {'str_field': {'default': 'extra'}}

        expected = dedent("""
            TestSerializer():
                id = ObjectIdField(read_only=True)
                str_field = CharField(default='extra')
        """)
        self.assertEqual(repr(TestSerializer()), expected)


    def test_invalid_field(self):
        """
        Field names that do not map to a model field or relationship should
        raise a configuration errror.
        """
        class TestSerializer(DocumentSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = ('id', 'invalid')

        with self.assertRaises(ImproperlyConfigured) as excinfo:
            TestSerializer().fields
        expected = 'Field name `invalid` is not valid for model `RegularFieldsModel`.'
        assert str(excinfo.exception) == expected

    def test_missing_field(self):
        """
        Fields that have been declared on the serializer class must be included
        in the `Meta.fields` if it exists.
        """
        class TestSerializer(DocumentSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel
                fields = ('id',)

        with self.assertRaises(AssertionError) as excinfo:
            TestSerializer().fields
        expected = (
            "The field 'missing' was declared on serializer TestSerializer, "
            "but has not been included in the 'fields' option."
        )
        assert str(excinfo.exception) == expected

    def test_missing_superclass_field_not_included(self):
        """
        Fields that have been declared on a parent of the serializer class may
        be excluded from the `Meta.fields` option.
        """
        class TestSerializer(DocumentSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel

        class ChildSerializer(TestSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel
                fields = ('id',)

        ChildSerializer().fields

    def test_missing_superclass_field_excluded(self):
        """
        Fields that have been declared on a parent of the serializer class may
        be excluded from the `Meta.fields` option.
        """
        class TestSerializer(DocumentSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel

        class ChildSerializer(TestSerializer):
            missing = serializers.ReadOnlyField()

            class Meta:
                model = RegularFieldsModel
                exclude = ('missing',)

        ChildSerializer().fields

    def test_choices_with_nonstandard_args(self):
        class ExampleSerializer(DocumentSerializer):
            class Meta:
                model = ChoicesModel

        ExampleSerializer()

    def test_fields_and_exclude_behavior(self):
        class ImplicitFieldsSerializer(DocumentSerializer):
            class Meta:
                model = RegularFieldsModel

        class ExplicitFieldsSerializer(DocumentSerializer):
            class Meta:
                model = RegularFieldsModel
                fields = '__all__'

        implicit = ImplicitFieldsSerializer()
        explicit = ExplicitFieldsSerializer()

        assert implicit.data == explicit.data
