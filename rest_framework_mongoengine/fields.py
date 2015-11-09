from collections import OrderedDict

from django.utils import six
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from bson import ObjectId, DBRef
from bson.errors import InvalidId

from mongoengine.queryset import QuerySet, QuerySetManager
from mongoengine.base.document import BaseDocument
from mongoengine import Document, fields as me_fields
from mongoengine.errors import DoesNotExist

from rest_framework_mongoengine.repr import smart_repr

class DocumentField(serializers.Field):
    """
    The field replicates DRF's `ModelField`.
    Base field for Mongoengine fields that we can not convert to DRF fields.

    A generic field that can be used against an arbitrary model field.

    This is used by `DocumentSerializer` when dealing with custom model fields,
    that do not have a serializer field to be mapped to.

    Delegates parsing to model_field.to_python.
    Representation is recursive with fallback to smart_repr.
    """

    type_label = 'DocumentField'

    def __init__(self, model_field, depth=0, **kwargs):
        self.model_field = model_field
        self.depth = depth
        super(DocumentField,self).__init__(**kwargs)

    def to_internal_value(self, data):
        return self.model_field.to_python(data)

    def to_representation(self, value):
        return self.transform_object(value, self.depth)

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
            return smart_repr(obj)
        elif isinstance(obj, BaseDocument):
            return self.transform_document(obj, depth)
        elif isinstance(obj, DBRef):
            # DBRef
            return self.transform_object(obj.id, depth)
        elif isinstance(obj, dict):
            # Dictionaries
            return self.transform_dict(obj, depth)
        elif isinstance(obj, list):
            # List
            return [self.transform_object(value, depth) for value in obj]
        elif obj is None:
            return None
        else:
            return smart_repr(obj)



class ObjectIdField(serializers.Field):
    type_label = 'ObjectIdField'

    def to_representation(self, value):
        return smart_str(value)

    def to_internal_value(self, data):
        try:
            return ObjectId(smart_str(data))
        except InvalidId:
            raise serializers.ValidationError("\"%s\" is not a valid ObjectId" % smart_str(data))


class ReferenceField(serializers.Field):
    """
    The field replicates DRF's `PrimaryKeyRelatedField` (w/out `many`).
    In particular, it checks value against existant objects and also provides choices.

    It serializes/parses str(bson.ObjectId). Internal value is bson.DBRef.
    """
    type_label = 'ReferenceField'
    default_error_messages = {
        'does_not_exist': _('Invalid id "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected str|ObjectId|DBRef|Document value, received {data_type}.'),
    }
    queryset = None
    pk_field_class = ObjectIdField

    def __init__(self, model=None, **kwargs):
        if model is not None:
            self.queryset = model.objects
        else:
            self.queryset = kwargs.pop('queryset', self.queryset)

        self.pk_field = self.pk_field_class()

        assert self.queryset is not None or kwargs.get('read_only', None), (
            'Reference field must provide a `queryset` or `model` argument, '
            'or set read_only=`True`.'
        )
        super(ReferenceField,self).__init__(**kwargs)

    def run_validation(self, data=empty):
        # We force empty strings to None values for relational fields.
        if data == '':
            data = None
        return super(ReferenceField,self).run_validation(data)

    def get_queryset(self):
        queryset = self.queryset
        if isinstance(queryset, (QuerySet, QuerySetManager)):
            # Ensure queryset is re-evaluated whenever used.
            # Note that actually a `Manager` class may also be used as the
            # queryset argument. This occurs on ModelSerializer fields,
            # as it allows us to generate a more expressive 'repr' output
            # for the field.
            # Eg: 'MyRelationship(queryset=ExampleModel.objects.all())'
            queryset = queryset.all()
        return queryset

    @property
    def choices(self):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        return OrderedDict([
            (
                six.text_type(self.to_representation(item)),
                self.display_value(item)
            )
            for item in queryset
        ])

    @property
    def grouped_choices(self):
        return self.choices

    def display_value(self, instance):
        return six.text_type(instance)

    def get_id(self, datum):
        if isinstance(datum, ObjectId):
            return datum
        elif isinstance(datum, (Document, DBRef)):
            return datum.id
        elif isinstance(datum, six.string_types):
            return self.pk_field.to_internal_value(datum)
        else:
            self.fail('incorrect_type', data_type=type(datum).__name__)

    def to_internal_value(self, datum):
        oid = self.get_id(datum)
        try:
            return self.get_queryset().only('id').get(id=oid).to_dbref()
        except DoesNotExist:
            self.fail('does_not_exist', pk_value=oid)

    def to_representation(self, datum):
        oid = self.get_id(datum)
        return self.pk_field.to_representation(oid)


class DynamicField(DocumentField):

    type_label = 'DynamicField'

    def __init__(self, field_name=None, source=None, *args, **kwargs):
        super(DynamicField, self).__init__(*args, **kwargs)
        self.field_name = field_name
        self.source = source
        if source:
            self.source_attrs = self.source.split('.')

    def to_representation(self, value):
        return self.model_field.to_python(value)



class BinaryField(DocumentField):

    type_label = 'BinaryField'

    def __init__(self, **kwargs):
        try:
            self.max_bytes = kwargs.pop('max_bytes')
        except KeyError:
            raise ValueError('BinaryField requires "max_bytes" kwarg')
        super(BinaryField, self).__init__(**kwargs)

    def to_representation(self, value):
        return smart_str(value)

    def to_internal_value(self, data):
        return super(BinaryField, self).to_internal_value(smart_str(data))


class BaseGeoField(DocumentField):

    type_label = 'BaseGeoField'
