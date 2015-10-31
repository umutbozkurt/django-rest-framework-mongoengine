import copy
from collections import OrderedDict

from mongoengine import fields as me_fields
from mongoengine.errors import ValidationError as me_ValidationError

from rest_framework import serializers
from rest_framework import fields as drf_fields
from rest_framework.utils.field_mapping import ClassLookupDict

from .fields import (ReferenceField, EmbeddedDocumentField, DynamicField,
                                               ObjectIdField, DocumentField, BinaryField, BaseGeoField)

from .utils import is_abstract_model, get_field_info, get_field_kwargs


def raise_errors_on_nested_writes(method_name, serializer, validated_data):
    """
    *** inherited from DRF 3, altered for EmbeddedDocumentSerializer to work automagically ***

    Give explicit errors when users attempt to pass writable nested data.

    If we don't do this explicitly they'd get a less helpful error when
    calling `.save()` on the serializer.

    We don't *automatically* support these sorts of nested writes because
    there are too many ambiguities to define a default behavior.

    Eg. Suppose we have a `UserSerializer` with a nested profile. How should
    we handle the case of an update, where the `profile` relationship does
    not exist? Any of the following might be valid:

    * Raise an application error.
    * Silently ignore the nested part of the update.
    * Automatically create a profile instance.
    """

    # Ensure we don't have a writable nested field. For example:
    #
    # class UserSerializer(ModelSerializer):
    #     ...
    #     profile = ProfileSerializer()
    assert not any(
        isinstance(field, serializers.BaseSerializer) and
        not isinstance(field, EmbeddedDocumentSerializer) and
        (key in validated_data)
        for key, field in serializer.fields.items()
    ), (
        'The `.{method_name}()` method does not support writable nested'
        'fields by default.\nWrite an explicit `.{method_name}()` method for '
        'serializer `{module}.{class_name}`, or set `read_only=True` on '
        'nested serializer fields.'.format(
            method_name=method_name,
            module=serializer.__class__.__module__,
            class_name=serializer.__class__.__name__
        )
    )

    # Ensure we don't have a writable dotted-source field. For example:
    #
    # class UserSerializer(ModelSerializer):
    #     ...
    #     address = serializer.CharField('profile.address')
    assert not any(
        '.' in field.source and (key in validated_data)
        and isinstance(validated_data[key], (list, dict))
        for key, field in serializer.fields.items()
    ), (
        'The `.{method_name}()` method does not support writable dotted-source '
        'fields by default.\nWrite an explicit `.{method_name}()` method for '
        'serializer `{module}.{class_name}`, or set `read_only=True` on '
        'dotted-source serializer fields.'.format(
            method_name=method_name,
            module=serializer.__class__.__module__,
            class_name=serializer.__class__.__name__
        )
    )


class DocumentSerializer(serializers.ModelSerializer):
    """
    Adaptation of ModelSerializer for mongoengine.
    """

    serializer_field_mapping = {
        me_fields.StringField: drf_fields.CharField,
        me_fields.URLField: drf_fields.URLField,
        me_fields.EmailField: drf_fields.EmailField,
        me_fields.IntField: drf_fields.IntegerField,
        me_fields.LongField: drf_fields.IntegerField,
        me_fields.FloatField: drf_fields.FloatField,
        me_fields.DecimalField: drf_fields.DecimalField,
        me_fields.BooleanField: drf_fields.BooleanField,
        me_fields.DateTimeField: drf_fields.DateTimeField,
        me_fields.ComplexDateTimeField: drf_fields.DateTimeField,
        me_fields.DynamicField: DynamicField,

        me_fields.ListField: drf_fields.ListField, # TODO
        me_fields.DictField: drf_fields.DictField, # TODO

        me_fields.EmbeddedDocumentField: EmbeddedDocumentField,
        me_fields.GenericEmbeddedDocumentField: EmbeddedDocumentField,

        me_fields.ObjectIdField: ObjectIdField,
        me_fields.ReferenceField: ReferenceField,
        me_fields.CachedReferenceField: ReferenceField,
        me_fields.GenericReferenceField: ReferenceField,

        me_fields.BinaryField: BinaryField,
        me_fields.FileField: drf_fields.FileField,
        me_fields.ImageField: drf_fields.ImageField,

        me_fields.SequenceField: drf_fields.IntegerField,
        me_fields.UUIDField: drf_fields.UUIDField,
        me_fields.GeoJsonBaseField: BaseGeoField
    }

    # induct failure if they occasionally used somewhere
    serializer_related_field = None
    serializer_related_to_field = None
    serializer_url_field = None

    def create(self, validated_data):
        """
        Create an instance using queryset.create()
        Before create() on self, call EmbeddedDocumentSerializer's create() first. If exists.
        """
        raise_errors_on_nested_writes('create', self, validated_data)

        # Automagically create and set embedded documents to validated data
        for embedded_field in self.embedded_document_serializer_fields:
            embedded_doc_intance = embedded_field.create(embedded_field.validated_data)
            validated_data[embedded_field.field_name] = embedded_doc_intance

        ModelClass = self.Meta.model
        try:
            instance = ModelClass(**validated_data)
            instance.save()
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
                    type(self).__name__,
                    exc
                )
            )
            raise TypeError(msg)
        except me_ValidationError as exc:
            msg = (
                'Got a `ValidationError` when calling `%s.objects.create()`. '
                'This may be because request data satisfies serializer validations '
                'but not Mongoengine`s. You may need to check consistency between '
                '%s and %s.\nIf that is not the case, please open a ticket '
                'regarding this issue on https://github.com/umutbozkurt/django-rest-framework-mongoengine/issues'
                '\nOriginal exception was: %s' %
                (
                    ModelClass.__name__,
                    ModelClass.__name__,
                    type(self).__name__,
                    exc
                )
            )
            raise me_ValidationError(msg)

        return instance

    def update(self, instance, validated_data):
        """
        Update embedded fields first, set relevant attributes with updated data
        And then continue regular updating
        """
        for embedded_field in self.embedded_document_serializer_fields:
            embedded_doc_intance = embedded_field.update(getattr(instance, embedded_field.field_name), embedded_field.validated_data)
            setattr(instance, embedded_field.field_name, embedded_doc_intance)

        return super(DocumentSerializer, self).update(instance, validated_data)


    def get_fields(self):
        """
        Return the dict of field names -> field instances that should be
        used for `self.fields` when instantiating the serializer.
        """

        assert hasattr(self, 'Meta'), (
            'Class {serializer_class} missing "Meta" attribute'.format(
                serializer_class=self.__class__.__name__
            )
        )
        assert hasattr(self.Meta, 'model'), (
            'Class {serializer_class} missing "Meta.model" attribute'.format(
                serializer_class=self.__class__.__name__
            )
        )
        if is_abstract_model(self.Meta.model):
            raise ValueError(
                'Cannot use ModelSerializer with Abstract Models.'
            )

        declared_fields = copy.deepcopy(self._declared_fields)
        model = getattr(self.Meta, 'model')
        depth = getattr(self.Meta, 'depth', 0)

        if depth is not None:
            assert depth >= 0, "'depth' may not be negative."
            assert depth <= 10, "'depth' may not be greater than 10."

        # Retrieve metadata about fields & relationships on the model class.
        info = get_field_info(model)
        field_names = self.get_field_names(declared_fields, info)

        # Determine any extra field arguments and hidden fields that
        # should be included
        extra_kwargs = self.get_extra_kwargs()
        extra_kwargs, hidden_fields = self.get_uniqueness_extra_kwargs(
            field_names, declared_fields, extra_kwargs
        )

        # Determine the fields that should be included on the serializer.
        fields = OrderedDict()

        for field_name in field_names:
            # If the field is explicitly declared on the class then use that.
            if field_name in declared_fields:
                fields[field_name] = declared_fields[field_name]
                continue

            # Determine the serializer field class and keyword arguments.
            field_class, field_kwargs = self.build_field(
                field_name, info, model, depth
            )

            # Include any kwargs defined in `Meta.extra_kwargs`
            extra_field_kwargs = extra_kwargs.get(field_name, {})
            field_kwargs = self.include_extra_kwargs(
                field_kwargs, extra_field_kwargs
            )

            # Create the serializer field.
            fields[field_name] = field_class(**field_kwargs)

        # Add in any hidden fields.
        fields.update(hidden_fields)

        return fields


    # def get_field_names(self, declared_fields, info):
    #     """
    #     Returns the list of all field names that should be created when
    #     instantiating this serializer class. This is based on the default
    #     set of fields, but also takes into account the `Meta.fields` or
    #     `Meta.exclude` options if they have been specified.
    #     """
    #     # use upstream
    #     pass

    # def get_default_field_names(self, declared_fields, model_info):
    #     """
    #     Return the default list of field names that will be used if the
    #     `Meta.fields` option is not specified.
    #     """
    #     # use upstream
    #     pass

    def build_field(self, field_name, info, model_class, nested_depth):
        """
        Return a two tuple of (cls, kwargs) to build a serializer field with.
        """
        # TODO
        if field_name in info.fields_and_pk:
            model_field = info.fields_and_pk[field_name]
            if isinstance(model_field, me_fields.ComplexBaseField):
                return self.build_compound_field(field_name, model_field)
            else:
                return self.build_standard_field(field_name, model_field)

        # TODO: handle reference fields in similar way
        # if field_name in info.relations:
        #     relation_info = info.relations[field_name]
        #     if not nested_depth:
        #         return self.build_relational_field(field_name, relation_info)
        #     else:
        #         return self.build_nested_field(field_name, relation_info, nested_depth)
        # TODO: handle embeddedfields here

        if hasattr(model_class, field_name):
            return self.build_property_field(field_name, model_class)

        return self.build_unknown_field(field_name, model_class)

    def build_standard_field(self, field_name, model_field):
        """
        Create regular model fields.
        """
        field_mapping = ClassLookupDict(self.serializer_field_mapping)

        field_class = field_mapping[model_field]
        field_kwargs = get_field_kwargs(field_name, model_field)

        if 'choices' in field_kwargs:
            # Fields with choices get coerced into `ChoiceField`
            # instead of using their regular typed field.
            field_class = self.serializer_choice_field
            # Some model fields may introduce kwargs that would not be valid
            # for the choice field. We need to strip these out.
            # Eg. models.DecimalField(max_digits=3, decimal_places=1, choices=DECIMAL_CHOICES)
            valid_kwargs = set((
                'read_only', 'write_only',
                'required', 'default', 'initial', 'source',
                'label', 'help_text', 'style',
                'error_messages', 'validators', 'allow_null', 'allow_blank',
                'choices'
            ))
            for key in list(field_kwargs.keys()):
                if key not in valid_kwargs:
                    field_kwargs.pop(key)

        if not issubclass(field_class, DocumentField):
            # `model_field` is only valid for the fallback case of
            # `ModelField`, which is used when no other typed field
            # matched to the model field.
            field_kwargs.pop('model_field', None)

        if not issubclass(field_class, drf_fields.CharField) and not issubclass(field_class, drf_fields.ChoiceField):
            # `allow_blank` is only valid for textual fields.
            field_kwargs.pop('allow_blank', None)

        if field_class is drf_fields.BooleanField and field_kwargs.get('allow_null', False):
            field_kwargs.pop('allow_null', None)
            field_kwargs.pop('default', None)
            field_class = drf_fields.NullBooleanField


        return field_class, field_kwargs

    def build_compound_field(self, field_name, model_field):
        """
        Create regular model fields.
        """
        # TODO
        pass

    def build_reference_field(self, field_name, relation_info):
        """
        Create fields for forward relationships.
        """
        # TODO from prototype build_relational_field
        pass

    def build_embedded_field(self, field_name, relation_info):
        """
        Create fields for embedded documents.
        """
        # TODO from prototype build_nested_field
        pass


    # def build_property_field(self, field_name, model_class):
    #     """
    #     Create a read only field for model methods and properties.
    #     """
    #     # use upstream

    # def build_unknown_field(self, field_name, model_class):
    #     """
    #     Raise an error on any unknown fields.
    #     """
    #     # use upastream

    # def include_extra_kwargs(self, kwargs, extra_kwargs):
    #     """
    #     Include any 'extra_kwargs' that have been included for this field,
    #     possibly removing any incompatible existing keyword arguments.
    #     """
    #     # use upastream

    # def get_extra_kwargs(self):
    #     """
    #     Return a dictionary mapping field names to a dictionary of
    #     additional keyword arguments.
    #     """
    #     # use mainstream

    def get_uniqueness_extra_kwargs(self, field_names, declared_fields, extra_kwargs):
        """
        Return any additional field options that need to be included as a
        result of uniqueness constraints on the model. This is returned as
        a two-tuple of:

        ('dict of updated extra kwargs', 'mapping of hidden fields')
        """
        # TODO
        return extra_kwargs, {}

    # def get_validators(self):
    #     """
    #     Determine the set of validators to use when instantiating serializer.
    #     """
    #     # mainstream

    def get_unique_together_validators(self):
        """
        Determine a default set of validators for any unique_together contraints.
        """
        # TODO
        return []

    def get_unique_for_date_validators(self):
        """
        Determine a default set of validators for the following contraints:

        * unique_for_date
        * unique_for_month
        * unique_for_year
        """
        # TODO
        return []


class DynamicDocumentSerializer(DocumentSerializer):
    # TODO
    pass


class EmbeddedDocumentSerializer(DocumentSerializer):
    # TODO
    pass
