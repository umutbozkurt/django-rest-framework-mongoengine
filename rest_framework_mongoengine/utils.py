from collections import namedtuple
from django.core.exceptions import ImproperlyConfigured
from django.utils import six

from mongoengine.base.common import get_document
from mongoengine.queryset import QuerySet
from mongoengine.errors import ValidationError
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
    # Deal with the primary key.
    pk = model.id if not issubclass(model, mongoengine.EmbeddedDocument) else None

    # Deal with regular fields.
    fields = OrderedDict()

    for field_name in model._fields_ordered:
        fields[field_name] = model._fields[field_name]

    # Deal with forward relationships.
    # Pass forward relations since there is no relations on mongodb
    forward_relations = OrderedDict()

    # Deal with reverse relationships.
    # Pass reverse relations since there is no relations on mongodb
    reverse_relations = OrderedDict()

    # Shortcut that merges both regular fields and the pk,
    # for simplifying regular field lookup.
    fields_and_pk = OrderedDict()
    fields_and_pk['pk'] = pk
    fields_and_pk[getattr(pk, 'name', 'pk')] = pk
    fields_and_pk.update(fields)

    # Shortcut that merges both forward and reverse relationships

    relations = OrderedDict(
        list(forward_relations.items()) +
        list(reverse_relations.items())
    )

    return FieldInfo(pk, fields, forward_relations, reverse_relations, fields_and_pk, relations)

def get_document_or_404(cls, *args, **kwargs):
    """
    Uses get() to return an document, or raises a Http404 exception if the document
    does not exist.

    cls may be a Document or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Note: Like with get(), an MultipleObjectsReturned will be raised if more than one
    object is found.

    Inspired by django.shortcuts.*
    """
    queryset = cls if isinstance(cls, QuerySet) else cls.objects

    try:
        return queryset.get(*args, **kwargs)
    except (queryset._document.DoesNotExist, ValidationError):
        from django.http import Http404
        raise Http404('No %s matches the given query.' % queryset._document._class_name)
