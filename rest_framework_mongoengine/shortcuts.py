#
# Added from mongoengine 0.9.0's django module
# https://github.com/MongoEngine/mongoengine/blob/0.9/mongoengine/django/shortcuts.py
#
# Removes dependency on mongoengine.django.shortcuts in generics.py when using mongoengine 0.9.x
# django module is removed in mongoengine 0.9.x
# https://github.com/MongoEngine/mongoengine/issues/958
#

from mongoengine.queryset import QuerySet
from mongoengine.base import BaseDocument
from mongoengine.errors import ValidationError

def _get_queryset(cls):
    """Inspired by django.shortcuts.*"""
    if isinstance(cls, QuerySet):
        return cls
    else:
        return cls.objects

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
    queryset = _get_queryset(cls)
    try:
        return queryset.get(*args, **kwargs)
    except (queryset._document.DoesNotExist, ValidationError):
        from django.http import Http404
        raise Http404('No %s matches the given query.' % queryset._document._class_name)

def get_list_or_404(cls, *args, **kwargs):
    """
    Uses filter() to return a list of documents, or raise a Http404 exception if
    the list is empty.

    cls may be a Document or QuerySet object. All other passed
    arguments and keyword arguments are used in the filter() query.

    Inspired by django.shortcuts.*
    """
    queryset = _get_queryset(cls)
    obj_list = list(queryset.filter(*args, **kwargs))
    if not obj_list:
        from django.http import Http404
        raise Http404('No %s matches the given query.' % queryset._document._class_name)
    return obj_list
