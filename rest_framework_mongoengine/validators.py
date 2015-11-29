from django.utils.translation import ugettext_lazy as _
from mongoengine.errors import ValidationError as mongo_ValidationError
from rest_framework import validators
from rest_framework.exceptions import ValidationError

class MongoValidationWrapper():
    def __init__(self, model_field):
        self.field = model_field

    def __call__(self, value):
        try:
            if self.field.validation:
                self.field.validation(value)
            if self.field.validate:
                self.field.validate(value)
        except mongo_ValidationError as e:
            raise ValidationError(e)


class ExcludeInstanceMixin():
    def exclude_current_instance(self, queryset):
        if self.instance is not None:
            return queryset.filter(pk__ne=self.instance.pk)
        return queryset


class UniqueValidator(ExcludeInstanceMixin, validators.UniqueValidator):
    pass


class UniqueTogetherValidator(ExcludeInstanceMixin, validators.UniqueTogetherValidator):
    pass
