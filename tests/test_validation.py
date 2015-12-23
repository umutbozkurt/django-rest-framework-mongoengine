from __future__ import unicode_literals

from django.test import TestCase
from mongoengine import Document, fields
from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer


class ValidatingModel(Document):
    name = fields.StringField()


class ValidationMethodSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingModel

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('Minimum 3 characters.')
        return value.title()


class RenamedValidationMethodSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingModel

    renamed = serializers.CharField(source='name', required=False)

    def validate_renamed(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('Minimum 3 characters.')
        return value.title()


def custom_field_validator(value):
    if len(value) < 3:
        raise serializers.ValidationError('Minimum 3 characters.')
    # cannot transform value


class FieldValidatorSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingModel

    name = serializers.CharField(validators=[custom_field_validator])


def custom_model_validator(data):
    if len(data['name']) < 3:
        raise serializers.ValidationError('Minimum 3 characters.')


class ModelValidatorSerializer(DocumentSerializer):
    class Meta:
        model = ValidatingModel
        validators = [custom_model_validator]


class TestValidating(TestCase):
    def test_validation_method_is_executed(self):
        serializer = ValidationMethodSerializer(data={'name': "fo"})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_validation_method_passing(self):
        serializer = ValidationMethodSerializer(data={'name': "foo"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], "Foo")

    def test_renamed_validation_method_is_executed(self):
        serializer = RenamedValidationMethodSerializer(data={'renamed': "fo"})
        self.assertFalse(serializer.is_valid())
        self.assertIn('renamed', serializer.errors)

    def test_renamed_validation_method_passing(self):
        serializer = RenamedValidationMethodSerializer(data={'renamed': "foo"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], "Foo")

    def test_validator_is_executed(self):
        serializer = FieldValidatorSerializer(data={'name': "fo"})
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)

    def test_validator_passing(self):
        serializer = FieldValidatorSerializer(data={'name': "foo"})
        self.assertTrue(serializer.is_valid())

    def test_validators_is_executed(self):
        serializer = ModelValidatorSerializer(data={'name': "fo"})
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_validators_passing(self):
        serializer = ModelValidatorSerializer(data={'name': "foo"})
        self.assertTrue(serializer.is_valid())
