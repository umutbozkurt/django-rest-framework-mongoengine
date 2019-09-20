from __future__ import unicode_literals

from rest_framework import validators
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SkipField

from rest_framework_mongoengine.repr import smart_repr


class MongoValidatorMixin():
    def exclude_current_instance(self, queryset):
        if self.instance is not None:
            return queryset.filter(pk__ne=self.instance.pk)
        return queryset


class UniqueValidator(MongoValidatorMixin, validators.UniqueValidator):
    """ Replacement of DRF UniqueValidator.

    Used by :class:`DocumentSerializer` for fields, present in unique indexes.
    """
    def __call__(self, value):
        queryset = self.queryset
        queryset = self.filter_queryset(value, queryset)
        queryset = self.exclude_current_instance(queryset)
        if queryset.first():
            raise ValidationError(self.message.format())

    def __repr__(self):
        return '<%s(queryset=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset)
        )


class UniqueTogetherValidator(MongoValidatorMixin, validators.UniqueTogetherValidator):
    """ Replacement of DRF UniqueTogetherValidator.

    Used by :class:`DocumentSerializer` for fields, present in unique indexes.
    """
    def __call__(self, attrs):
        try:
            self.enforce_required_fields(attrs)
        except SkipField:
            return
        queryset = self.queryset
        queryset = self.filter_queryset(attrs, queryset)
        queryset = self.exclude_current_instance(queryset)
        # Ignore validation if any field is None
        checked_values = [
            value for field, value in attrs.items() if field in self.fields
        ]
        if None not in checked_values and queryset.first():
            field_names = ', '.join(self.fields)
            raise ValidationError(self.message.format(field_names=field_names))

    def __repr__(self):
        return '<%s(queryset=%s, fields=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.queryset),
            smart_repr(self.fields)
        )


class OptionalUniqueTogetherValidator(UniqueTogetherValidator):
    """
    This validator passes validation if all of validation fields are missing. (for use with partial data)
    """
    def enforce_required_fields(self, attrs):
        try:
            super(OptionalUniqueTogetherValidator, self).enforce_required_fields(attrs)
        except ValidationError as e:
            if set(e.detail.keys()) == set(self.fields):
                raise SkipField()
            else:
                raise
