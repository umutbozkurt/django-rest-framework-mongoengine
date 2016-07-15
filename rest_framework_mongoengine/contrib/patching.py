import re

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import DictField, ListSerializer


def get_field_for_path(serializer, path):
    head = path[0]
    tail = path[1:]

    if hasattr(serializer, 'fields'):
        serializer = serializer.fields[head]
    elif hasattr(serializer, 'child'):
        serializer = serializer.child
    else:
        raise KeyError(head)

    if len(tail):
        return get_field_for_path(serializer, tail)
    else:
        return serializer


class PatchItem(DictField):
    """ just a dict with keys: path, op, value """
    def to_internal_value(self, value):
        value = super(PatchItem, self).to_internal_value(value)
        if set(value.keys()) != set(['op', 'path', 'value']):
            raise ValidationError("Missing some of required parts: 'path', 'op', 'value'")
        if value['path'][0] != '/':
            raise ValidationError({'path': "Invalid path"})
        value['path'] = tuple(value['path'].split('/')[1:])

        if self.parent.serializer:
            try:
                field = get_field_for_path(self.parent.serializer, value['path'])
            except KeyError as e:
                raise ValidationError({'path': "Missing elem: '%s'" % e.args[0]})

            if value['op'] in ('set', 'inc', 'dec'):
                if field is not None:
                    value['value'] = field.to_internal_value(value['value'])
            elif value['op'] in ('push', 'pull', 'add_to_set'):
                field = getattr(field, 'child')
                if field is not None:
                    value['value'] = field.to_internal_value(value['value'])
            elif value['op'] in ('unset', 'pull_all', 'min', 'max'):
                if value['value'] is not None:
                    raise ValidationError({'value': "Value for '%s' expected to be null" % value['op']})
            elif value['op'] in ('pop',):
                try:
                    value['value'] = int(value['value'])
                except:
                    raise ValidationError({'value': "Integer expected for '%s'" % value['op']})

        return value

idx_re = re.compile("^(\d+|S)$")


class Patch(ListSerializer):
    """ RFC 6902 json-patch

    patch := [ item ]
    item := {
        path: str -- path to attribute, starting with "/"
        op: str -- mongo update operator
        value: any -- argument to operator
    }
    """
    child = PatchItem()

    def __init__(self, serializer=None, *args, **kwargs):
        self.serializer = serializer if serializer is not None else None
        super(Patch, self).__init__(*args, **kwargs)

    def update_queryset(self, queryset):
        # appply all items in sequence, to avoid semeobj modification at the same query
        for item in self.validated_data:
            update = {item['op'] + "__" + ("__".join(item['path'])): item['value']}
            queryset.update(**update)


class PatchModelMixin():
    """
    Patch model instance, or requested filtered queryset.

    Route PATCH request method to `modify_obj` or `modify_set`. Override `perform_modify` if necessary.

    Default methods return 204 no content.
    """
    def modify_set(self, request, *args, **kwargs):
        return self.modify_queryset(request, self.filter_queryset(self.get_queryset()))

    def modify_obj(self, request, *args, **kwargs):
        return self.modify_queryset(request, self.get_object())

    def modify_queryset(self, request, queryset):
        patch = Patch(self.get_serializer(), data=request.data)
        patch.is_valid(raise_exception=True)
        self.perform_modify(queryset, patch)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_modify(self, queryset, patch):
        """ actually perform update on queryset """
        patch.update_queryset(queryset)
