from rest_framework.serializers import ListSerializer, DictField
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status


class PatchItem(DictField):
    def to_internal_value(self, value):
        value = super(PatchItem, self).to_internal_value(value)
        if set(value.keys()) != set(['op', 'path', 'value']):
            raise ValidationError("Missing some of required parts: 'path', 'op', 'value'")
        if value['path'][0] != '/':
            raise ValidationError("Invalid path")

        fld = "__".join(value['path'].split('/')[1:])
        key = value['op'] + "__" + fld
        arg = value['value']
        return (key, arg)

    def to_representation(self, value):
        return {value[0]: value[1]}


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

    def update_queryset(self, queryset):
        # maybe merged for optimizaion, if keys are unique
        for k, v in self.validated_data:
            queryset.update(**{k: v})


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
        patch = Patch(data=request.data)
        patch.is_valid(raise_exception=True)
        self.perform_modify(queryset, patch)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_modify(self, queryset, patch):
        """ actually perform update on queryset """
        patch.update_queryset(queryset)
