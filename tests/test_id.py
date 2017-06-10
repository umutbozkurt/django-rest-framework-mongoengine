from django.test import TestCase
from mongoengine import ValidationError as me_ValidationError
from mongoengine import Document, fields
from rest_framework import serializers

from rest_framework_mongoengine.serializers import DocumentSerializer


# How "id" works in mongoengine
# -----------------------------
#
# In mongoengine models "id" field works as follows:
# If there's a field with primart_key=True, id refers to that field.
# Otherwise, mongoengine automatically creates an
# id = ObjectIdField(primary_key=True, db_ref="_id") on Document.
# See mongoengine's: base/metaclasses.py:TopLevelDocumentMetaclass.
#
# There's a way to shoot yourself in the leg with this behavior of id:
# you can define a field, named "id", on your mongoengine Document, but
# not set primary_key=True on it. In that case mongoengine will create a field
# "_id" in the database and a model field, named id, that will refer to that
# database field, but also will create a database field "id" that can't be
# accessed from mongoengine side. I believe, this is a bug of mongoengine.
#
# Don't do this, kids!

class CustomIdModel(Document):
    id = fields.StringField(primary_key=True)


class CustomIdSerializer(DocumentSerializer):
    id = serializers.CharField()

    class Meta:
        model = CustomIdModel
        fields = '__all__'


class IncorrectSerializer(DocumentSerializer):
    """This serializer doesn't override id field, thus it is incorrect."""
    class Meta:
        model = CustomIdModel
        fields = '__all__'


class IncorrectSerializerTestCase(TestCase):
    data = {
        "id": "foo"
    }

    def doCleanups(self):
        CustomIdModel.drop_collection()

    def test_incorrect(self):
        """This test shows that if we've overridden id field on a model and
        haven't explicitly specified an id field on serializer, like in
        IncorrectSerializer, the serializer successfully passes DRFME
        validation, but Mongoengine validation raises a ValidationError
        with a puzzling error message.

        We need a more explicit error message here, which tells DRFME user to
        override id field on serializer; don't know, how to implement this.
        """
        serializer = IncorrectSerializer(data=self.data)
        assert serializer.is_valid()
        with self.assertRaises(me_ValidationError):
            serializer.save()
#        #print "serializer.fields = %s" % serializer.fields
#        #print "serializer.validated_data = %s" % serializer.validated_data
#        #serializer.save()
#
#    def test_readable(self):
#        serializer = IncorrectSerializer()


class CustomIdTestCase(TestCase):
    data = {
        "id": "foo"
    }

    def doCleanups(self):
        CustomIdModel.drop_collection()

    def test_get(self):
        pass
