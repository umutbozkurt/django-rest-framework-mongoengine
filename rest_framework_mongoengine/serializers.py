from __future__ import unicode_literals
import warnings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import FieldDoesNotExist
from mongoengine.errors import ValidationError
from rest_framework import serializers
from mongoengine import fields as me_fields
from django.core.paginator import Page
from django.db import models
from django.forms import widgets

from collections import OrderedDict
import copy

from rest_framework_mongoengine.utils import get_field_info

from .fields import ReferenceField, ListField, EmbeddedDocumentField, DynamicField, ObjectIdField
from rest_framework import fields as drf_fields
from rest_framework.utils.field_mapping import get_field_kwargs


class MongoEngineModelSerializer(serializers.ModelSerializer):
    """
    Model Serializer that supports Mongoengine
    """
    MAX_RECURSION_DEPTH = 5  # default value of depth

    field_mapping = {
        me_fields.FloatField: drf_fields.FloatField,
        me_fields.IntField: drf_fields.IntegerField,
        me_fields.DateTimeField: drf_fields.DateTimeField,
        me_fields.EmailField: drf_fields.EmailField,
        me_fields.URLField: drf_fields.URLField,
        me_fields.StringField: drf_fields.CharField,
        me_fields.BooleanField: drf_fields.BooleanField,
        me_fields.FileField: drf_fields.FileField,
        me_fields.ImageField: drf_fields.ImageField,
        me_fields.ObjectIdField: ObjectIdField,
        me_fields.ReferenceField: ReferenceField,
        me_fields.ListField: ListField,
        me_fields.EmbeddedDocumentField: EmbeddedDocumentField,
        me_fields.DynamicField: DynamicField,
        me_fields.DecimalField: drf_fields.DecimalField,
        me_fields.UUIDField: drf_fields.CharField
    }

    def get_validators(self):
        validators = getattr(getattr(self, 'Meta', None), 'validators', [])
        return validators

    # def perform_validation(self, attrs):
    #     """
    #     Rest Framework built-in validation + related model validations
    #     """
    #     for field_name, field in self.fields.items():
    #         if field_name in self._errors:
    #             continue
    #
    #         source = field.source or field_name
    #         if self.partial and source not in attrs:
    #             continue
    #
    #         if field_name in attrs and hasattr(field, 'model_field'):
    #             try:
    #                 field.model_field.validate(attrs[field_name])
    #             except ValidationError as err:
    #                 self._errors[field_name] = str(err)
    #
    #         try:
    #             validate_method = getattr(self, 'validate_%s' % field_name, None)
    #             if validate_method:
    #                 attrs = validate_method(attrs, source)
    #         except serializers.ValidationError as err:
    #             self._errors[field_name] = self._errors.get(field_name, []) + list(err.messages)
    #
    #     if not self._errors:
    #         try:
    #             attrs = self.validate(attrs)
    #         except serializers.ValidationError as err:
    #             if hasattr(err, 'message_dict'):
    #                 for field_name, error_messages in err.message_dict.items():
    #                     self._errors[field_name] = self._errors.get(field_name, []) + list(error_messages)
    #             elif hasattr(err, 'messages'):
    #                 self._errors['non_field_errors'] = err.messages
    #
    #     return attrs

    # def restore_object(self, attrs, instance=None):
    #     if instance is None:
    #         instance = self.opts.model()
    #
    #     dynamic_fields = self.get_dynamic_fields(instance)
    #     all_fields = dict(dynamic_fields, **self.fields)
    #
    #     for key, val in attrs.items():
    #         field = all_fields.get(key)
    #         if not field or field.read_only:
    #             continue
    #
    #         if isinstance(field, serializers.Serializer):
    #             many = field.many
    #
    #             def _restore(field, item):
    #                 # looks like a bug, sometimes there are decerialized objects in attrs
    #                 # sometimes they are just dicts
    #                 if isinstance(item, BaseDocument):
    #                     return item
    #                 return field.from_native(item)
    #
    #             if many:
    #                 val = [_restore(field, item) for item in val]
    #             else:
    #                 val = _restore(field, val)
    #
    #         key = getattr(field, 'source', None) or key
    #         try:
    #             setattr(instance, key, val)
    #         except ValueError:
    #             self._errors[key] = self.error_messages['required']
    #
    #     return instance

    def get_fields(self):
        declared_fields = copy.deepcopy(self._declared_fields)

        ret = OrderedDict()
        model = getattr(self.Meta, 'model')
        fields = getattr(self.Meta, 'fields', None)
        exclude = getattr(self.Meta, 'exclude', None)
        depth = getattr(self.Meta, 'depth', 0)
        extra_kwargs = getattr(self.Meta, 'extra_kwargs', {})

        if fields and not isinstance(fields, (list, tuple)):
            raise TypeError(
                'The `fields` option must be a list or tuple. Got %s.' %
                type(fields).__name__
            )

        if exclude and not isinstance(exclude, (list, tuple)):
            raise TypeError(
                'The `exclude` option must be a list or tuple. Got %s.' %
                type(exclude).__name__
            )

        assert not (fields and exclude), "Cannot set both 'fields' and 'exclude'."

        extra_kwargs = self._include_additional_options(extra_kwargs)

        # # Retrieve metadata about fields & relationships on the model class.
        info = get_field_info(model)

        # Use the default set of field names if none is supplied explicitly.
        if fields is None:
            fields = self._get_default_field_names(declared_fields, info)
            exclude = getattr(self.Meta, 'exclude', None)
            if exclude is not None:
                for field_name in exclude:
                    fields.remove(field_name)

        # Determine the set of model fields, and the fields that they map to.
        # We actually only need this to deal with the slightly awkward case
        # of supporting `unique_for_date`/`unique_for_month`/`unique_for_year`.
        model_field_mapping = {}
        for field_name in fields:
            if field_name in declared_fields:
                field = declared_fields[field_name]
                source = field.source or field_name
            else:
                try:
                    source = extra_kwargs[field_name]['source']
                except KeyError:
                    source = field_name
            # Model fields will always have a simple source mapping,
            # they can't be nested attribute lookups.
            if '.' not in source and source != '*':
                model_field_mapping[source] = field_name

        # Determine if we need any additional `HiddenField` or extra keyword
        # arguments to deal with `unique_for` dates that are required to
        # be in the input data in order to validate it.
        hidden_fields = {}

        # Now determine the fields that should be included on the serializer.
        for field_name in fields:
            if field_name in declared_fields:
                # Field is explicitly declared on the class, use that.
                ret[field_name] = declared_fields[field_name]
                continue

            elif field_name in info.fields_and_pk:
                # Create regular model fields.
                model_field = info.fields_and_pk[field_name]
                field_cls = self.field_mapping[model_field.__class__]
                kwargs = self.get_field_kwargs(model_field)
                if 'choices' in kwargs:
                    # Fields with choices get coerced into `ChoiceField`
                    # instead of using their regular typed field.
                    field_cls = drf_fields.ChoiceField
                if not issubclass(field_cls, drf_fields.CharField) and not issubclass(field_cls, drf_fields.ChoiceField):
                    # `allow_blank` is only valid for textual fields.
                    kwargs.pop('allow_blank', None)

            elif hasattr(model, field_name):
                # Create a read only field for model methods and properties.
                field_cls = drf_fields.ReadOnlyField
                kwargs = {}

            else:
                raise ImproperlyConfigured(
                    'Field name `%s` is not valid for model `%s`.' %
                    (field_name, model.__class__.__name__)
                )

            # Check that any fields declared on the class are
            # also explicitly included in `Meta.fields`.
            missing_fields = set(declared_fields.keys()) - set(fields)
            if missing_fields:
                missing_field = list(missing_fields)[0]
                raise ImproperlyConfigured(
                    'Field `%s` has been declared on serializer `%s`, but '
                    'is missing from `Meta.fields`.' %
                    (missing_field, self.__class__.__name__)
                )

            # Populate any kwargs defined in `Meta.extra_kwargs`
            extras = extra_kwargs.get(field_name, {})
            if extras.get('read_only', False):
                for attr in [
                    'required', 'default', 'allow_blank', 'allow_null',
                    'min_length', 'max_length', 'min_value', 'max_value',
                    'validators', 'queryset'
                ]:
                    kwargs.pop(attr, None)

            if extras.get('default') and kwargs.get('required') is False:
                kwargs.pop('required')

            kwargs.update(extras)

            # Create the serializer field.
            ret[field_name] = field_cls(**kwargs)

        for field_name, field in hidden_fields.items():
            ret[field_name] = field

        return ret

    def get_dynamic_fields(self, document):
        dynamic_fields = {}
        if document is not None and document._dynamic:
            for name, field in document._dynamic_fields.items():
                dynamic_fields[name] = DynamicField(field_name=name, source=name, **self.get_field_kwargs(field))
        return dynamic_fields

    def get_field_kwargs(self, model_field):
        kwargs = {}

        if type(model_field) in (me_fields.ReferenceField, me_fields.EmbeddedDocumentField,
                                     me_fields.ListField, me_fields.DynamicField):
            kwargs['model_field'] = model_field
            kwargs['depth'] = getattr(self.Meta, 'depth', self.MAX_RECURSION_DEPTH)

        if type(model_field) is me_fields.ObjectIdField:
            kwargs['required'] = False
        else:
            kwargs['required'] = model_field.required

        if type(model_field) is me_fields.EmbeddedDocumentField:
            kwargs['document_type'] = model_field.document_type

        if model_field.default:
            kwargs['required'] = False
            kwargs['default'] = model_field.default

        if model_field.__class__ == models.TextField:
            kwargs['widget'] = widgets.Textarea

        attribute_dict = {
            me_fields.StringField: ['max_length'],
            me_fields.DecimalField: ['min_value', 'max_value'],
            me_fields.EmailField: ['max_length'],
            me_fields.FileField: ['max_length'],
            me_fields.URLField: ['max_length'],
        }

        if model_field.__class__ in attribute_dict:
            attributes = attribute_dict[model_field.__class__]
            for attribute in attributes:
                kwargs.update({attribute: getattr(model_field, attribute)})

        return kwargs

    def create(self, validated_data):
        ModelClass = self.Meta.model
        try:
            instance = ModelClass.objects.create(**validated_data)
        except TypeError as exc:
            msg = (
                'Got a `TypeError` when calling `%s.objects.create()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.objects.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception text was: %s.' %
                (
                    ModelClass.__name__,
                    ModelClass.__name__,
                    self.__class__.__name__,
                    exc
                )
            )
            raise TypeError(msg)

        return instance

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        Serialize regular + dynamic fields
        """
        ret = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]
        fields += self.get_dynamic_fields(instance).values()

        for field in fields:
            attribute = field.get_attribute(instance)
            if attribute is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret

    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        ret = super(MongoEngineModelSerializer, self).to_internal_value(data)
        [drf_fields.set_value(ret, [k], data[k]) for k in data if k not in ret]
        return ret


    # @property
    # def data(self):
    #     """
    #     Returns the serialized data on the serializer.
    #     """
    #     if self._data is None:
    #         obj = self.object
    #
    #         if self.many is not None:
    #             many = self.many
    #         else:
    #             many = hasattr(obj, '__iter__') and not isinstance(obj, (mongoengine.BaseDocument, Page, dict))
    #             if many:
    #                 warnings.warn('Implicit list/queryset serialization is deprecated. '
    #                               'Use the `many=True` flag when instantiating the serializer.',
    #                               DeprecationWarning, stacklevel=2)
    #
    #         if many:
    #             self._data = [self.to_native(item) for item in obj]
    #         else:
    #             self._data = self.to_native(obj)
    #
    #     return self._data