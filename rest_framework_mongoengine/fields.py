from bson.errors import InvalidId
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_str
from mongoengine import dereference
from mongoengine.base.document import BaseDocument
from mongoengine.document import Document
from rest_framework import serializers


class MongoDocumentField(serializers.WritableField):
    MAX_RECURSION_DEPTH = 5  # default value of depth

    def __init__(self, *args, **kwargs):
        try:
            self.model_field = kwargs.pop('model_field')
            self.depth = kwargs.pop('depth', self.MAX_RECURSION_DEPTH)
        except KeyError:
            raise ValueError("%s requires 'model_field' kwarg" % self.type_label)

        super(MongoDocumentField, self).__init__(*args, **kwargs)

    def transform_document(self, document, depth):
        data = {}

        # serialize each required field
        for field in document._fields:
            if hasattr(document, smart_str(field)):
                # finally check for an attribute 'field' on the instance
                obj = getattr(document, field)
            else:
                continue

            val = self.transform_object(obj, depth-1)

            if val is not None:
                data[field] = val

        return data

    def transform_dict(self, obj, depth):
        return dict([(key, self.transform_object(val, depth-1))
                     for key, val in obj.items()])

    def transform_object(self, obj, depth):
        """
        Models to natives
        Recursion for (embedded) objects
        """
        if depth == 0:
            return "Max recursion depth exceeded"
        elif isinstance(obj, BaseDocument):
            # Document, EmbeddedDocument
            return self.transform_document(obj, depth-1)
        elif isinstance(obj, dict):
            # Dictionaries
            return self.transform_dict(obj, depth-1)
        elif isinstance(obj, list):
            # List
            return [self.transform_object(value, depth-1) for value in obj]
        else:
            # Default to string
            return unicode(obj)


class ReferenceField(MongoDocumentField):

    type_label = 'ReferenceField'

    def from_native(self, value):
        try:
            dbref = self.model_field.to_python(value)
        except InvalidId:
            raise ValidationError(self.error_messages['invalid'])

        instance = dereference.DeReference().__call__([dbref])[0]

        # Check if dereference was successful
        if not isinstance(instance, Document):
            msg = self.error_messages['invalid']
            raise ValidationError(msg)

        return instance

    def to_native(self, obj):
        return self.transform_object(obj, self.depth)


class ListField(MongoDocumentField):

    type_label = 'ListField'

    def from_native(self, value):
        return self.model_field.to_python(value)

    def to_native(self, obj):
        return self.transform_object(obj, self.depth)


class EmbeddedDocumentField(MongoDocumentField):

    type_label = 'EmbeddedDocumentField'

    def __init__(self, *args, **kwargs):
        try:
            self.document_type = kwargs.pop('document_type')
        except KeyError:
            raise ValueError("EmbeddedDocumentField requires 'document_type' kwarg")

        super(EmbeddedDocumentField, self).__init__(*args, **kwargs)

    def get_default_value(self):
        return self.to_native(self.default())

    def from_native(self, obj):
        print obj
        if not obj:
            return self.get_default_value()
        return self.document_type(**obj)


class DynamicField(MongoDocumentField):

    type_label = 'DynamicField'

    def to_native(self, obj):
        return self.transform_object(obj, self.MAX_RECURSION_DEPTH)