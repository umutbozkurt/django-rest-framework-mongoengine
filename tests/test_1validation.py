from __future__ import unicode_literals

import pytest
from django.test import TestCase

from mongoengine import Document, fields

from rest_framework import serializers
from rest_framework_mongoengine.serializers import DocumentSerializer


class ShouldValidateModel(Document):
    should_validate_field = fields.StringField()


class ShouldValidateModelSerializer(DocumentSerializer):
    renamed = serializers.CharField(source='should_validate_field', required=False)

    def validate_renamed(self, value):
        if len(value) < 3:
            raise serializers.ValidationError('Minimum 3 characters.')
        return value

    class Meta:
        model = ShouldValidateModel
        fields = ('renamed',)


class TestPreSaveValidationExclusionsSerializer(TestCase):
    def test_renamed_fields_are_model_validated(self):
        """
        Ensure fields with 'source' applied do get still get model validation.
        """
        # We've set `required=False` on the serializer, but the model
        # does not have `blank=True`, so this serializer should not validate.
        serializer = ShouldValidateModelSerializer(data={'renamed': ''})
        self.assertEqual(serializer.is_valid(), False)
        self.assertIn('renamed', serializer.errors)
        self.assertNotIn('should_validate_field', serializer.errors)


class TestCustomValidationMethods(TestCase):
    def test_custom_validation_method_is_executed(self):
        serializer = ShouldValidateModelSerializer(data={'renamed': 'fo'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('renamed', serializer.errors)

    def test_custom_validation_method_passing(self):
        serializer = ShouldValidateModelSerializer(data={'renamed': 'foo'})
        self.assertTrue(serializer.is_valid())
