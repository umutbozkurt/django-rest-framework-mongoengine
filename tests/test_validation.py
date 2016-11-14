from __future__ import unicode_literals

from django.test import TestCase
from rest_framework import serializers

from rest_framework_mongoengine.serializers import DocumentSerializer

from .models import DumbDocument


class ValidationMethodSerializer(DocumentSerializer):
    class Meta:
        model = DumbDocument
        fields = '__all__'

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('Minimum 3 characters.')
        return value.title()


class RenamedValidationMethodSerializer(DocumentSerializer):
    class Meta:
        model = DumbDocument
        fields = '__all__'

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
        model = DumbDocument
        fields = '__all__'

    name = serializers.CharField(validators=[custom_field_validator])


def custom_model_validator(data):
    if len(data['name']) < 3:
        raise serializers.ValidationError('Minimum 3 characters.')


class ModelValidatorSerializer(DocumentSerializer):
    class Meta:
        model = DumbDocument
        fields = '__all__'
        validators = [custom_model_validator]


class TestValidating(TestCase):
    def test_validation_method_is_executed(self):
        serializer = ValidationMethodSerializer(data={'name': "fo"})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_validation_method_passing(self):
        serializer = ValidationMethodSerializer(data={'name': "foo"})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['name'] == "Foo"

    def test_renamed_validation_method_is_executed(self):
        serializer = RenamedValidationMethodSerializer(data={'renamed': "fo"})
        assert not serializer.is_valid()
        assert 'renamed' in serializer.errors

    def test_renamed_validation_method_passing(self):
        serializer = RenamedValidationMethodSerializer(data={'renamed': "foo"})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['name'] == "Foo"

    def test_validator_is_executed(self):
        serializer = FieldValidatorSerializer(data={'name': "fo"})
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_validator_passing(self):
        serializer = FieldValidatorSerializer(data={'name': "foo"})
        assert serializer.is_valid(), serializer.errors

    def test_validators_is_executed(self):
        serializer = ModelValidatorSerializer(data={'name': "fo"})
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

    def test_validators_passing(self):
        serializer = ModelValidatorSerializer(data={'name': "foo"})
        assert serializer.is_valid(), serializer.errors
