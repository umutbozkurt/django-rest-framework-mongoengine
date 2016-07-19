from django.test import TestCase
from mongoengine import ValidationError as me_ValidationError
from mongoengine import Document, fields
from rest_framework import serializers

from rest_framework_mongoengine.serializers import DocumentSerializer


class CustomIdModel(Document):
    id = fields.StringField(primary_key=True)


class CustomIdSerializer(DocumentSerializer):
    id = serializers.CharField()

    class Meta:
        model = CustomIdModel


class IncorrectSerializer(DocumentSerializer):
    '''This serializer doesn't override id field, thus it is incorrect.'''
    class Meta:
        model = CustomIdModel


class IncorrectSerializerTestCase(TestCase):
    data = {
        "id": "foo"
    }

    def doCleanups(self):
        CustomIdModel.drop_collection()

    def test_incorrect(self):
        serializer = IncorrectSerializer(data=self.data)
        assert serializer.is_valid()
        with self.assertRaises(me_ValidationError):
            serializer.save()


class CustomIdTestCase(TestCase):
    def doCleanups(self):
        CustomIdModel.drop_collection()
