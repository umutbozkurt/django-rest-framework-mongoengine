"""
Helper functions for creating user-friendly representations
of serializer classes and serializer fields.
"""
from __future__ import unicode_literals

import re

from django.utils.encoding import force_str
from mongoengine.base import BaseDocument
from mongoengine.fields import BaseField
from mongoengine.queryset import QuerySet
from rest_framework.fields import Field

from rest_framework_mongoengine.fields import DictField


def manager_repr(value):
    model = value._document
    return '%s.objects' % (model.__name__,)


def mongo_field_repr(value):
    # mimic django models.Field.__repr__
    path = '%s.%s' % (value.__class__.__module__, value.__class__.__name__)
    name = getattr(value, 'name', None)
    if name is not None:
        return '<%s: %s>' % (path, name)
    return '<%s>' % path


def mongo_doc_repr(value):
    # mimic django models.Model.__repr__
    try:
        u = str(value)
    except (UnicodeEncodeError, UnicodeDecodeError):
        u = '[Bad Unicode data]'
    return force_str('<%s: %s>' % (value.__class__.__name__, u))


uni_lit_re = re.compile("u'(.*?)'")


def smart_repr(value):
    if isinstance(value, QuerySet):
        return manager_repr(value)

    if isinstance(value, BaseField):
        return mongo_field_repr(value)

    if isinstance(value, BaseDocument):
        return mongo_field_repr(value)

    if isinstance(value, Field):
        return field_repr(value)

    value = repr(value)

    # Representations like u'help text'
    # should simply be presented as 'help text'
    value = uni_lit_re.sub("'\\1'", value)

    # Representations like
    # <django.core.validators.RegexValidator object at 0x1047af050>
    # Should be presented as
    # <django.core.validators.RegexValidator object>
    value = re.sub(' at 0x[0-9a-f]{4,32}>', '>', value)

    return value


def field_repr(field, force_many=False):
    kwargs = field._kwargs
    if force_many:
        kwargs = kwargs.copy()
        kwargs['many'] = True
        kwargs.pop('child', None)

    if kwargs.get('label', None) is None:
        kwargs.pop('label', None)
    if kwargs.get('help_text', None) is None:
        kwargs.pop('help_text', None)

    arg_string = ', '.join([smart_repr(val) for val in field._args])
    kwarg_string = ', '.join([
        '%s=%s' % (key, smart_repr(val))
        for key, val in sorted(kwargs.items())
    ])
    if arg_string and kwarg_string:
        arg_string += ', '

    if force_many:
        class_name = force_many.__class__.__name__
    else:
        class_name = field.__class__.__name__

    return "%s(%s%s)" % (class_name, arg_string, kwarg_string)


def serializer_repr(serializer, indent, force_many=None):
    ret = field_repr(serializer, force_many) + ':'
    indent_str = '    ' * indent

    if force_many:
        fields = force_many.fields
    else:
        fields = serializer.fields

    for field_name, field in fields.items():
        ret += '\n' + indent_str + field_name + ' = '
        if hasattr(field, 'fields'):
            ret += serializer_repr(field, indent + 1)
        elif hasattr(field, 'child') and not isinstance(field, DictField):
            ret += list_repr(field, indent + 1)
        elif hasattr(field, 'child') and isinstance(field, DictField):
            ret += dict_repr(field, indent)
        else:
            ret += field_repr(field)

    if serializer.validators:
        ret += '\n' + indent_str + 'class Meta:'
        ret += '\n' + indent_str + '    validators = ' + smart_repr(serializer.validators)

    if len(fields) == 0:
        ret += "\npass"

    return ret


def list_repr(serializer, indent):
    child = serializer.child
    if hasattr(child, 'fields'):
        return serializer_repr(serializer, indent, force_many=child)
    return field_repr(serializer)


def dict_repr(serializer, indent):
    ret = field_repr(serializer)

    child = serializer.child
    if hasattr(child, 'fields'):
        ret = field_repr(serializer) + ":"
        ser_repr = serializer_repr(child, indent + 1)
        ret += "\n" + ser_repr.split("\n", 1)[1]  # chop the name of seiralizer off

    return ret
