from collections import namedtuple
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from mongoengine.base.common import get_document
import mongoengine

from rest_framework.compat import OrderedDict
from rest_framework.utils import field_mapping
import inspect


FieldInfo = namedtuple('FieldResult', [
    'pk',  # Model field instance
    'fields',  # Dict of field name -> model field instance
    'forward_relations',  # Dict of field name -> RelationInfo
    'reverse_relations',  # Dict of field name -> RelationInfo
    'fields_and_pk',  # Shortcut for 'pk' + 'fields'
    'relations'  # Shortcut for 'forward_relations' + 'reverse_relations'
])

RelationInfo = namedtuple('RelationInfo', [
    'model_field',
    'related',
    'to_many',
    'has_through_model'
])


def _resolve_model(obj):
    """
    Inherited from rest_framework.utils.model_meta
    Overridden for MongoDB compability
    """
    if isinstance(obj, six.string_types) and len(obj.split('.')) == 2:
        app_name, model_name = obj.split('.')
        resolved_model = get_document(model_name)
        if resolved_model is None:
            msg = "Mongoengine did not return a model for {0}.{1}"
            raise ImproperlyConfigured(msg.format(app_name, model_name))
        return resolved_model
    elif inspect.isclass(obj) and issubclass(obj, mongoengine.BaseDocument):
        return obj
    raise ValueError("{0} is not a MongoDB Document".format(obj))


def get_field_info(model):
    """
    Given a model class, returns a `FieldInfo` instance containing metadata
    about the various field types on the model.
    """
    opts = model._meta

    # Deal with the primary key.
    pk = model.id

    # Deal with regular fields.
    fields = OrderedDict()

    for field_name in model._fields_ordered:
        fields[field_name] = model._fields[field_name]

    # Deal with forward relationships.
    forward_relations = OrderedDict()

    # Deal with reverse relationships.
    reverse_relations = OrderedDict()

    # Shortcut that merges both regular fields and the pk,
    # for simplifying regular field lookup.
    fields_and_pk = OrderedDict()
    fields_and_pk['pk'] = pk
    fields_and_pk[pk.name] = pk
    fields_and_pk.update(fields)

    # Shortcut that merges both forward and reverse relationships

    relations = OrderedDict(
        list(forward_relations.items()) +
        list(reverse_relations.items())
    )

    return FieldInfo(pk, fields, forward_relations, reverse_relations, fields_and_pk, relations)