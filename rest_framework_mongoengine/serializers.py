from __future__ import unicode_literals
import warnings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields import FieldDoesNotExist
from mongoengine.errors import ValidationError
from rest_framework import serializers
from rest_framework import fields
import mongoengine
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
        mongoengine.FloatField: fields.FloatField,
        mongoengine.IntField: fields.IntegerField,
        mongoengine.DateTimeField: fields.DateTimeField,
        mongoengine.EmailField: fields.EmailField,
        mongoengine.URLField: fields.URLField,
        mongoengine.StringField: fields.CharField,
        mongoengine.BooleanField: fields.BooleanField,
        mongoengine.FileField: fields.FileField,
        mongoengine.ImageField: fields.ImageField,
        mongoengine.ObjectIdField: ObjectIdField,
        mongoengine.ReferenceField: ReferenceField,
        mongoengine.ListField: ListField,
        mongoengine.EmbeddedDocumentField: EmbeddedDocumentField,
        mongoengine.DynamicField: DynamicField,
        mongoengine.DecimalField: fields.DecimalField,
        mongoengine.UUIDField: fields.CharField
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
        unique_constraint_names = set()
            #
            # # Include each of the `unique_for_*` field names.
            # unique_constraint_names |= set([
            #     model_field.unique_for_date,
            #     model_field.unique_for_month,
            #     model_field.unique_for_year
            # ])

        # unique_constraint_names -= set([None])
        #
        # # Include each of the `unique_together` field names,
        # # so long as all the field names are included on the serializer.
        # for parent_class in [model] + list(model._meta.parents.keys()):
        #     for unique_together_list in parent_class._meta.unique_together:
        #         if set(fields).issuperset(set(unique_together_list)):
        #             unique_constraint_names |= set(unique_together_list)
        #
        # # Now we have all the field names that have uniqueness constraints
        # # applied, we can add the extra 'required=...' or 'default=...'
        # # arguments that are appropriate to these fields, or add a `HiddenField` for it.
        # for unique_constraint_name in unique_constraint_names:
        #     # Get the model field that is referred too.
        #     unique_constraint_field = model._meta.get_field(unique_constraint_name)
        #
        #     if getattr(unique_constraint_field, 'auto_now_add', None):
        #         default = CreateOnlyDefault(timezone.now)
        #     elif getattr(unique_constraint_field, 'auto_now', None):
        #         default = timezone.now
        #     elif unique_constraint_field.has_default():
        #         default = unique_constraint_field.default
        #     else:
        #         default = empty
        #
        #     if unique_constraint_name in model_field_mapping:
        #         # The corresponding field is present in the serializer
        #         if unique_constraint_name not in extra_kwargs:
        #             extra_kwargs[unique_constraint_name] = {}
        #         if default is empty:
        #             if 'required' not in extra_kwargs[unique_constraint_name]:
        #                 extra_kwargs[unique_constraint_name]['required'] = True
        #         else:
        #             if 'default' not in extra_kwargs[unique_constraint_name]:
        #                 extra_kwargs[unique_constraint_name]['default'] = default
        #     elif default is not empty:
        #         # The corresponding field is not present in the,
        #         # serializer. We have a default to use for it, so
        #         # add in a hidden field that populates it.
        #         hidden_fields[unique_constraint_name] = HiddenField(default=default)

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

    def get_default_fields(self):
        cls = self.opts.model
        opts = self.Meta
        fields = [getattr(opts, field) for field in cls._fields_ordered]

        ret = OrderedDict()

        for model_field in fields:
            if isinstance(model_field, mongoengine.ObjectIdField):
                field = self.get_pk_field(model_field)
            else:
                field = self.get_field(model_field)

            if field:
                field.bind(model_field.name, self)
                ret[model_field.name] = field

        for field_name in self.opts.read_only_fields:
            assert field_name in ret, "read_only_fields on '%s' included invalid item '%s'" % \
                                      (self.__class__.__name__, field_name)
            ret[field_name].read_only = True

        return ret

    def get_dynamic_fields(self, obj):
        dynamic_fields = {}
        if obj is not None and obj._dynamic:
            for key, value in obj._dynamic_fields.items():
                dynamic_fields[key] = self.get_field_kwargs(value)
        return dynamic_fields

    def get_field_kwargs(self, model_field):
        kwargs = {}

        if model_field.__class__ in (mongoengine.ReferenceField, mongoengine.EmbeddedDocumentField,
                                     mongoengine.ListField, mongoengine.DynamicField):
            kwargs['model_field'] = model_field
            kwargs['depth'] = getattr(self.Meta, 'depth', self.MAX_RECURSION_DEPTH)

        if not model_field.__class__ == mongoengine.ObjectIdField:
            kwargs['required'] = model_field.required

        if model_field.__class__ == mongoengine.EmbeddedDocumentField:
            kwargs['document_type'] = model_field.document_type

        if model_field.default:
            kwargs['required'] = False
            kwargs['default'] = model_field.default

        if model_field.__class__ == models.TextField:
            kwargs['widget'] = widgets.Textarea

        attribute_dict = {
            mongoengine.StringField: ['max_length'],
            mongoengine.DecimalField: ['min_value', 'max_value'],
            mongoengine.EmailField: ['max_length'],
            mongoengine.FileField: ['max_length'],
            mongoengine.URLField: ['max_length'],
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

    # def to_representation(self, instance):
    #     """
    #     Rest framework built-in to_native + transform_object
    #     """
    #     ret = self._dict_class()
    #     ret.fields = self._dict_class()
    #
    #     #Dynamic Document Support
    #     dynamic_fields = self.get_dynamic_fields(instance)
    #     all_fields = self._dict_class()
    #     all_fields.update(self.fields)
    #     all_fields.update(dynamic_fields)
    #
    #     for field_name, field in all_fields.items():
    #         if field.read_only and instance is None:
    #             continue
    #         field.initialize(parent=self, field_name=field_name)
    #         key = self.get_field_key(field_name)
    #         value = field.field_to_native(instance, field_name)
    #         if not getattr(field, 'write_only', False):
    #             ret[key] = value
    #         ret.fields[key] = self.augment_field(field, field_name, key, value)
    #
    #     return ret
    #
    # def to_internal_value(self, data):
    #     self._errors = {}
    #
    #     if data is not None:
    #         attrs = self.restore_fields(data)
    #         for key in data.keys():
    #             if key not in attrs:
    #                 attrs[key] = data[key]
    #         if attrs is not None:
    #             attrs = self.perform_validation(attrs)
    #     else:
    #         self._errors['non_field_errors'] = ['No input provided']
    #
    #     if not self._errors:
    #         return self.restore_object(attrs, instance=getattr(self, 'object', None))

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