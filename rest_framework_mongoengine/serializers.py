from __future__ import unicode_literals
import warnings
from rest_framework import serializers
from rest_framework import fields
from bson import DBRef
from mongoengine import dereference
import mongoengine
from mongoengine.base import BaseDocument
from django.db import models
from django.forms import widgets
from django.utils.datastructures import SortedDict
from rest_framework.compat import get_concrete_model


class MongoEngineModelSerializerOptions(serializers.ModelSerializerOptions):
    """
    Meta class options for MongoEngineModelSerializer
    """
    def __init__(self, meta):
        super(MongoEngineModelSerializerOptions, self).__init__(meta)
        self.validations = getattr(meta, 'related_model_validations', {})


class MongoEngineModelSerializer(serializers.ModelSerializer):
    """
    Model Serializer that supports Mongoengine
    """
    _options_class = MongoEngineModelSerializerOptions

    def validate_related_field(self, attrs, source, object_type):
        """
        Validate related model
        """
        value = attrs[source]

        try:
            object_type.objects.get(pk=value)
        except object_type.DoesNotExist:
            raise serializers.ValidationError(object_type.__name__ + ' with PK ' + value + ' does not exists.')
        return attrs

    def perform_validation(self, attrs):
        """
        Rest Framework built-in validation + related model validations
        """
        for field_name, field in self.fields.items():
            if field_name in self._errors:
                continue

            source = field.source or field_name
            if self.partial and source not in attrs:
                continue

            # Related Model Validations
            if field_name in self.opts.validations:
                try:
                    self.validate_related_field(attrs, source, self.opts.validations[field_name])
                except serializers.ValidationError as err:
                    self._errors[field_name] = self._errors.get(field_name, []) + list(err.messages)

            try:
                validate_method = getattr(self, 'validate_%s' % field_name, None)
                if validate_method:
                    attrs = validate_method(attrs, source)
            except serializers.ValidationError as err:
                self._errors[field_name] = self._errors.get(field_name, []) + list(err.messages)

        if not self._errors:
            try:
                attrs = self.validate(attrs)
            except serializers.ValidationError as err:
                if hasattr(err, 'message_dict'):
                    for field_name, error_messages in err.message_dict.items():
                        self._errors[field_name] = self._errors.get(field_name, []) + list(error_messages)
                elif hasattr(err, 'messages'):
                    self._errors['non_field_errors'] = err.messages

        return attrs

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            for key, val in attrs.items():
                try:
                    setattr(instance, key, val)
                except ValueError:
                    self._errors[key] = self.error_messages['required']

        else:
            instance = self.opts.model(**attrs)
        return instance

    def get_default_fields(self):
        cls = self.opts.model
        opts = get_concrete_model(cls)
        fields = []
        fields += [getattr(opts, field) for field in opts._fields]

        ret = SortedDict()

        for model_field in fields:
            if isinstance(model_field, mongoengine.ObjectIdField):
                field = self.get_pk_field(model_field)
            else:
                field = self.get_field(model_field)

            if field:
                field.initialize(parent=self, field_name=model_field.name)
                ret[model_field.name] = field

        for field_name in self.opts.read_only_fields:
            assert field_name in ret,\
            "read_only_fields on '%s' included invalid item '%s'" %\
            (self.__class__.__name__, field_name)
            ret[field_name].read_only = True

        return ret

    def get_field(self, model_field):
        kwargs = {}

        if model_field.required:
            kwargs['required'] = False

        if model_field.default:
            kwargs['required'] = False
            kwargs['default'] = model_field.default

        if model_field.__class__ == models.TextField:
            kwargs['widget'] = widgets.Textarea

        field_mapping = {
            mongoengine.FloatField: fields.FloatField,
            mongoengine.IntField: fields.IntegerField,
            mongoengine.DateTimeField: fields.DateTimeField,
            mongoengine.EmailField: fields.EmailField,
            mongoengine.URLField: fields.URLField,
            mongoengine.StringField: fields.CharField,
            mongoengine.BooleanField: fields.BooleanField,
            mongoengine.FileField: fields.FileField,
            mongoengine.ImageField: fields.ImageField,
            mongoengine.ObjectIdField: fields.Field,
            mongoengine.ReferenceField: fields.CharField,
        }

        attribute_dict = {
            mongoengine.StringField: ['max_length'],
            mongoengine.DecimalField: ['max_digits', 'decimal_places'],
            mongoengine.EmailField: ['max_length'],
            mongoengine.FileField: ['max_length'],
            mongoengine.ImageField: ['max_length'],
            mongoengine.URLField: ['max_length'],
        }

        if model_field.__class__ in attribute_dict:
            attributes = attribute_dict[model_field.__class__]
            for attribute in attributes:
                kwargs.update({attribute: getattr(model_field, attribute)})

        try:
            return field_mapping[model_field.__class__](**kwargs)
        except KeyError:
            return fields.ModelField(model_field=model_field, **kwargs)

    def transform_object(self, obj, fields, depth):
        """
        Models to natives
        Recursion for embedded models
        """
        object_data = obj._data
        counter = 0
        emb_obj_count = 0

        for field in fields:
            if issubclass(object_data[field].__class__, DBRef) or issubclass(object_data[field].__class__, mongoengine.Document):
                emb_obj_count += 1

        for field in fields:
            if depth == 0:
                    object_data = unicode(object_data['id'])
                    break
            elif issubclass(object_data[field].__class__, DBRef):
                object_data = dereference.DeReference().__call__(object_data)
                if counter < depth*emb_obj_count:
                    counter += 1
                    object_data[field] = self.transform_object(object_data[field], object_data[field]._fields, depth-1)
                else:
                    object_data[field] = unicode(object_data[field].pk)
            elif issubclass(object_data[field].__class__, mongoengine.Document):
                if counter < depth*emb_obj_count:
                    counter += 1
                    object_data[field] = self.transform_object(object_data[field], object_data[field]._fields, depth-1)
                else:
                    object_data[field] = unicode(object_data[field].pk)
            else:
                object_data[field] = unicode(object_data[field])

        return object_data

    def to_native(self, obj):
        """
        Rest framework built-in to_native + transform_object
        """
        ret = self._dict_class()
        ret.fields = self._dict_class()
        depth = self.opts.depth

        for field_name, field in self.fields.items():
            if field.read_only and obj is None:
                continue
            field.initialize(parent=self, field_name=field_name)
            key = self.get_field_key(field_name)
            value = field.field_to_native(obj, field_name)
            #Support for custom fields, check key exists on default fields
            if key in obj._data:
                #Call transform_object if field is a related model
                if issubclass(obj._data[key].__class__, mongoengine.Document) or isinstance(obj._data[key], DBRef):
                    value = self.transform_object(obj._data[key], value, depth)
            #Override value with transform_ methods
            method = getattr(self, 'transform_%s' % field_name, None)
            if callable(method):
                value = method(obj, value)
            if not getattr(field, 'write_only', False):
                ret[key] = value
            ret.fields[key] = self.augment_field(field, field_name, key, value)

        return ret

    def from_native(self, data, files=None):
        self._errors = {}

        if data is not None or files is not None:
            attrs = self.restore_fields(data, files)
            if attrs is not None:
                attrs = self.perform_validation(attrs)
        else:
            self._errors['non_field_errors'] = ['No input provided']

        if not self._errors:
            return self.restore_object(attrs, instance=getattr(self, 'object', None))

    @property
    def data(self):
        """
        Returns the serialized data on the serializer.
        """
        if self._data is None:
            obj = self.object

            if self.many is not None:
                many = self.many
            else:
                many = hasattr(obj, '__iter__') and not isinstance(obj, (BaseDocument, Page, dict))
                if many:
                    warnings.warn('Implicit list/queryset serialization is deprecated. '
                                  'Use the `many=True` flag when instantiating the serializer.',
                                  DeprecationWarning, stacklevel=2)

            if many:
                self._data = [self.to_native(item) for item in obj]
            else:
                self._data = self.to_native(obj)

        return self._data
