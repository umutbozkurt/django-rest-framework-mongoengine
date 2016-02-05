from collections import OrderedDict, namedtuple

import mongoengine
from django.utils.text import capfirst
from mongoengine import fields as me_fields
from rest_framework.utils.field_mapping import needs_label

from rest_framework_mongoengine.validators import UniqueValidator

FieldInfo = namedtuple('FieldResult', [
    'pk',  # Model field instance
    'fields',  # Dict of field name -> model field instance, contains fieldname.child for compound fields
    'references',  # Dict of field name -> RelationInfo
    'fields_and_pk',  # Shortcut for 'pk' + 'fields'
    'embedded'  # Dict of field name -> RelationInfo
])

RelationInfo = namedtuple('RelationInfo', [
    'model_field',
    'related_model'
])


NUMERIC_FIELD_TYPES = (
    me_fields.IntField,
    me_fields.LongField,
    me_fields.FloatField,
    me_fields.DecimalField
)

REFERENCING_FIELD_TYPES = (
    me_fields.ReferenceField,
    me_fields.CachedReferenceField,
    me_fields.GenericReferenceField
)

EMBEDDING_FIELD_TYPES = (
    me_fields.EmbeddedDocumentField,
    me_fields.GenericEmbeddedDocumentField
)

COMPOUND_FIELD_TYPES = (
    me_fields.DictField,
    me_fields.ListField
)


def get_relation_info(model_field):
    return RelationInfo(
        model_field=model_field,
        related_model=getattr(model_field, 'document_type', None),
    )


def get_field_info(model):
    """
    Given a model class, returns a `FieldInfo` instance, which is a
    `namedtuple`, containing metadata about the various field types on the model
    including information about their relationships.
    """
    # Deal with the primary key.
    if issubclass(model, mongoengine.EmbeddedDocument):
        pk = None
    else:
        pk = model._fields[model._meta['id_field']]

    # Deal with regular fields.
    fields = OrderedDict()

    # Deal with forward relationships.
    # Pass forward relations since there is no relations on mongodb
    references = OrderedDict()

    embedded = OrderedDict()

    def add_field(name, field):
        if isinstance(field, REFERENCING_FIELD_TYPES):
            references[name] = get_relation_info(field)
        elif isinstance(field, EMBEDDING_FIELD_TYPES):
            embedded[name] = get_relation_info(field)
        elif isinstance(field, COMPOUND_FIELD_TYPES):
            fields[name] = field
            if field.field:
                add_field(name + '.child', field.field)
        elif field is pk:
            return
        else:
            fields[name] = field

    for field_name in model._fields_ordered:
        add_field(field_name, model._fields[field_name])

    # Shortcut that merges both regular fields and the pk,
    # for simplifying regular field lookup.
    fields_and_pk = OrderedDict()
    fields_and_pk['pk'] = pk
    fields_and_pk[getattr(pk, 'name', 'pk')] = pk
    fields_and_pk.update(fields)

    return FieldInfo(pk,
                     fields,
                     references,
                     fields_and_pk,
                     embedded)


def is_abstract_model(model):
    return hasattr(model, 'meta') and model.meta.get('abstract', False)


def get_field_kwargs(field_name, model_field):
    """
    Creates a default instance of a basic non-relational field.
    """
    kwargs = {}

    # The following will only be used by ModelField classes.
    # Gets removed for everything else.
    kwargs['model_field'] = model_field

    if hasattr(model_field, 'verbose_name') and needs_label(model_field, field_name):
        kwargs['label'] = capfirst(model_field.verbose_name)

    if hasattr(model_field, 'help_text'):
        kwargs['help_text'] = model_field.help_text

    if isinstance(model_field, me_fields.DecimalField):
        precision = model_field.precision
        max_value = getattr(model_field, 'max_value', None)
        if max_value is not None:
            max_length = len(str(max_value)) + precision
        else:
            max_length = 65536
        kwargs['decimal_places'] = precision
        kwargs['max_digits'] = max_length

    if isinstance(model_field, me_fields.GeoJsonBaseField):
        kwargs['geo_type'] = model_field._type

    if isinstance(model_field, me_fields.SequenceField) or model_field.primary_key or model_field.db_field == '_id':
        # If this field is read-only, then return early.
        # Further keyword arguments are not valid.
        kwargs['read_only'] = True
        return kwargs

    kwargs['required'] = model_field.required

    if model_field.default:
        kwargs['required'] = False

    if model_field.default and not isinstance(model_field, me_fields.ComplexBaseField):
        kwargs['default'] = model_field.default

    if model_field.null:
        kwargs['allow_null'] = True

    if model_field.choices:
        # If this model field contains choices, then return early.
        # Further keyword arguments are not valid.
        kwargs['choices'] = model_field.choices
        return kwargs

    max_length = getattr(model_field, 'max_length', None)
    if max_length is not None and isinstance(model_field, me_fields.StringField):
        kwargs['max_length'] = max_length

    min_length = getattr(model_field, 'min_length', None)
    if min_length is not None and isinstance(model_field, me_fields.StringField):
        kwargs['min_length'] = min_length

    max_value = getattr(model_field, 'max_value', None)
    if max_value is not None and isinstance(model_field, NUMERIC_FIELD_TYPES):
        kwargs['max_value'] = max_value

    min_value = getattr(model_field, 'min_value', None)
    if min_value is not None and isinstance(model_field, NUMERIC_FIELD_TYPES):
        kwargs['min_value'] = min_value

    return kwargs


def get_relation_kwargs(field_name, relation_info):
    """
    Creates a default instance of a flat relational field.
    """
    model_field, related_model = relation_info
    kwargs = {}
    if related_model:
        kwargs['queryset'] = related_model.objects
    else:
        kwargs['read_only'] = True

    if model_field:
        if hasattr(model_field, 'verbose_name') and needs_label(model_field, field_name):
            kwargs['label'] = capfirst(model_field.verbose_name)
        if hasattr(model_field, 'help_text'):
            kwargs['help_text'] = model_field.help_text
        if kwargs.get('read_only', False):
            # If this field is read-only, then return early.
            # No further keyword arguments are valid.
            return kwargs

        if model_field.default or model_field.null:
            kwargs['required'] = False
        if model_field.null:
            kwargs['allow_null'] = True
        if getattr(model_field, 'unique', False):
            validator = UniqueValidator(queryset=model_field.model.objects)
            kwargs['validators'] = [validator]

    return kwargs


def has_default(model_field):
    return model_field.default is not None or model_field.null
