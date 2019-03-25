from typing import Type

from django.db.models import Model
from django_alt.validators import Validator

from django_alt.contexts import RequestContext


class ValidatedManager:
    def __init__(self, model_class: Type[Model],
                 validator_class: Type[Validator], context: Type[RequestContext] = None, **kwargs):
        self.request_context = context
        self.model_class = model_class
        self.validator_class = validator_class
        self.validator = None

    def make_validator(self, attrs, **kwargs):
        kwargs.setdefault('model', self.model_class)
        kwargs.setdefault('context', self.request_context)
        self.validator = self.validator_class(attrs, **kwargs)
        return self.validator

    def validate_only(self):
        assert self.validator is not None, (
            'You have to call `make_validator` on `{}` before explicitly calling `validate_only`.'
        ).format(self.__class__.__name__)
        self.validator.pre()

        self.validator.clean_and_default_fields()
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
            self.make_validator(attrs, is_create=True)
            self.validate_only()
        elif len(attrs):
            self.validator._is_create = True
            self.validator.attrs = attrs

        self.validator.will_create()
        self.validator.will_create_or_update()
        self.validator.base_db()

        instance = self.create_instance()

        self.validator.did_create(instance)
        self.validator.did_create_or_update(instance)
        self.validator.post()

        return instance

    def do_create_many(self, list_of_attrs, object_manager=None):
        list_of_validators = []
        for attrs in list_of_attrs:
            validator = self.make_validator(attrs, is_create=True)
            self.validate_only()
            list_of_validators.append(validator)

        for validator in list_of_validators:
            validator.will_create()
            validator.will_create_or_update()
            validator.base_db()

        object_manager = self.model_class.objects if not object_manager else object_manager
        list_of_instances = object_manager.bulk_create(
            self.model_class(**validator.attrs) for validator in list_of_validators
        )

        for validator, instance in zip(list_of_validators, list_of_instances):
            validator.did_create(instance)
            validator.did_create_or_update(instance)
            self.validator.post()

        return list_of_instances

    def create_instance(self):
        return self.model_class.objects.create(**self.validator.attrs) if self.model_class is not None else None

    def do_update(self, instance, **attrs):
        """
        Validates given attribute dict and replaces fields of
        an existing object with its contents.
        :param instance: instance to update
        :param attrs: attributes to update the object with
        :return: updated instance
        """
        if self.validator is None:
            self.make_validator(attrs, is_create=False)
            self.validate_only()
        elif len(attrs):
            self.validator._is_create = False
            self.validator.attrs = attrs

        self.validator.will_update(instance)
        self.validator.will_create_or_update()
        self.validator.base_db()

        instance = self.update_instance(instance)

        self.validator.did_update(instance)
        self.validator.did_create_or_update(instance)
        self.validator.post()

        return instance

    def update_instance(self, instance):
        for k, v in self.validator.attrs.items():
            setattr(instance, k, v)
        instance.save()
        return instance

    def _do_delete_pre(self, queryset, **attrs):
        if self.validator is None:
            self.make_validator(attrs)
            self.validator.pre()

        self.validator.will_delete(queryset)

    def _do_delete_post(self, queryset, **attrs):
        self.validator.did_delete(queryset)
        self.validator.post()
        return queryset

    def delete_instance(self, instance):
        assert instance is not None, (
            'An instance was not passed to `{}` for deletion\n'
            'but `delete` was called.'
            'Did you forget to include a `query` clause in an endpoint `delete` config?'
        ).format(self.__class__.__qualname__)
        return instance.delete()

    def do_delete(self, queryset, **attrs):
        """
        Validates given attribute dict and calls delete on given queryset.
        :param queryset: object instance(s) to delete
        :param attrs: extra attributes to pass to the validation engine
        :return: deleted instance(s)
        """
        self._do_delete_pre(queryset, **attrs)
        queryset = self.delete_instance(queryset)
        self._do_delete_post(queryset, **attrs)
        return queryset
