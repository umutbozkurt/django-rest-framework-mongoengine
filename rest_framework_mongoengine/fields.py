"""
The module description
"""
from collections import OrderedDict

from django.utils import six
from django.utils.encoding import is_protected_type, smart_text
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from bson import ObjectId, DBRef
from bson.errors import InvalidId

from mongoengine.base import get_document
from mongoengine.errors import ValidationError as MongoValidationError, NotRegistered

from mongoengine.queryset import QuerySet, QuerySetManager
from mongoengine import EmbeddedDocument, Document, fields as me_fields
from mongoengine.errors import DoesNotExist

from rest_framework_mongoengine.repr import smart_repr


class ObjectIdField(serializers.Field):
    """ Field for ObjectId value """
    type_label = 'ObjectIdField'

    def to_internal_value(self, value):
        try:
            return ObjectId(smart_text(value))
        except InvalidId:
            raise serializers.ValidationError("%s is not a valid ObjectId" % repr(value))

    def to_representation(self, value):
        return smart_text(value)


class DocumentField(serializers.Field):
    """ Replacement of DRF ModelField
    Keeps track of underlying document field.
    Delegates parsing nd validation to underlying document field.

    Used by DocumentSerializers to map unknown fields.
    """
    type_label = 'DocumentField'

    def __init__(self, model_field, **kwargs):
        self.model_field = model_field
        super(DocumentField, self).__init__(**kwargs)

    def get_attribute(self, obj):
        return obj

    def to_internal_value(self, data):
        """ convert input to python value
        Uses underlying document field's `to_python` method.
        """
        return self.model_field.to_python(data)

    def to_representation(self, obj):
        """ convert value to representation
        DRF ModelField uses `value_to_string` for this purpose. Mongoengine fields do not have such method.

        This implementation uses `django.utils.encoding.smart_text` to convert everything to text, while keeping json-safe types intact.

        NB: The argument is whole object instead of value. It's upstream feature.
        """
        value = self.model_field.__get__(obj, None)
        return smart_text(value, strings_only=True)

    def run_validators(self, value):
        try:
            self.model_field.validate(value)
        except MongoValidationError as e:
            raise ValidationError(e.message)
        super(DocumentField, self).run_validators()


class GenericField(serializers.Field):
    """ Field for generic value
    Tries to handle values of arbitrary type.
    """
    type_label = 'GenericField'

    default_error_messages = {
        'undefined_model': _('`{doc_cls}` has not been defined.')
    }

    def to_representation(self, value):
        """ convert value to representation
        Recursively transforms dicts, lists and embedded docs.
        Embedded docs are serialized into dicts with additional attribute `_cls`.
        Primitive types represented using `django.utils.encoding.smart_text`, keeping json-safe intact.
        """
        return self.represent_data(value)

    def represent_data(self, data):
        if isinstance(data, EmbeddedDocument):
            return self.represent_document(data)
        elif isinstance(data, DBRef):
            return smart_text(data.id)
        elif isinstance(data, dict):
            return dict([(key, self.represent_data(val)) for key, val in data.items()])
        elif isinstance(data, list):
            return [self.represent_data(value) for value in data]
        elif data is None:
            return None
        else:
            return smart_text(data, strings_only=True)

    def represent_document(self, doc):
        data = { '_cls': doc.__class__.__name__}
        for field in doc._fields:
            if not hasattr(doc, field):
                continue
            data[field] = self.represent_data(getattr(doc, field))
        return data

    def to_internal_value(self, value):
        """ convert input into value
        Recursively transforms dicts, lists and embedded docs.
        Any dict with item '_cls' is converted to registered EmbeddedDocument.
        Anything else left intact.
        """
        return self.parse_data(value)

    def parse_data(self, data):
        if isinstance(data, dict):
            result = dict([(key, self.parse_data(val)) for key, val in data.items()])
            if '_cls' in result:
                try:
                    doc_name = result['_cls']
                    doc_cls = get_document(doc_name)
                    return doc_cls._from_son(result)
                except NotRegistered:
                    self.fail('undefined_model', doc_cls=doc_name)
            else:
                return result
        elif isinstance(data, list):
            return [self.parse_data(value) for value in data]
        else:
            return data


class DynamicField(GenericField, DocumentField):
    """ Field for DynamicDocuments
    Used internally by `DynamicDocumentSerializer`.
    Behaves like `GenericField`.
    """


class ReferenceField(serializers.Field):
    """ Serialization of ReferenceField.
    Behaves like DRF ForeignKeyField.
    """
    type_label = 'ReferenceField'
    default_error_messages = {
        'does_not_exist': _('Invalid id "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected str|ObjectId|DBRef|Document value, received {data_type}.'),
    }
    queryset = None

    pk_field_class = ObjectIdField
    """ serializer field class used to handle object ids """

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
