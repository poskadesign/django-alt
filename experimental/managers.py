from django.db.models import Model
from typing import Type

from experimental.validators import Validator


class ValidatedManager:
    def __init__(self, model_class: Type[Model], validator_class: Type[Validator], **context):
        self.context = context
        self.model_class = model_class
        self.validator_class = validator_class
        self.validator = None

    def make_validator(self, **attrs):
        self.validator = self.validator_class(attrs, model=self.model_class, **self.context)
        return self.validator

    def validate_only(self, **attrs):
        self.make_validator(**attrs)
        self.validator.clean_fields()
        self.validator.clean()

        self.validator.base()
        self.validator.validate_fields()
        self.validator.validate_checks()
        return self.validator.attrs

    def do_create(self, **attrs):
        """
        Validates given attribute dict and creates an object from it.
        :param attrs: attributes to create the object from
        :return: created instance
        """
        if self.validator is None:
            self.validate_only(**attrs)
        elif len(attrs):
            raise AssertionError((
                'Attempting to pass `attrs` when validator was already instantiated.\n'
                'If you explicitly call `validate_only`, do not pass any parameters to `do_create`.\n'
                'Offending manager: `{} ({})`.'
            ).format(self.__class__.__name__, self.__class__.__qualname__))

        self.validator.will_create()
        self.validator.base_db()

        instance = self.model_class.objects.create(**self.validator.attrs)

        self.validator.did_create(instance)
        return instance

    def do_update(self, instance, **attrs):
        """
        Validates given attribute dict and replaces fields of
        an existing object with its contents.
        :param instance: instance to update
        :param attrs: attributes to update the object with
        :return: updated instance
        """
        if self.validator is None:
            self.validate_only(**attrs)
        elif len(attrs):
            raise AssertionError((
                'Attempting to pass `attrs` when validator was already instantiated.\n'
                'If you explicitly call `validate_only`, do not pass any parameters to `do_update`.\n'
                'Offending manager: `{} ({})`.'
            ).format(self.__class__.__name__, self.__class__.__qualname__))

        self.validator.will_update(instance)
        self.validator.base_db()

        for k, v in self.validator.attrs.items():
            setattr(instance, k, v)
        instance.save()

        self.validator.did_update(instance)
        return instance

    def do_delete(self, queryset, **attrs):
        """
        Validates given attribute dict and calls delete on given queryset.
        :param queryset: object instance(s) to delete
        :param attrs: extra attributes to pass to the validation engine
        :return: deleted instance(s)
        """
        self.make_validator(**attrs)
        self.validator.will_delete(queryset)
        queryset.delete()
        self.validator.did_delete(queryset)
        return queryset
