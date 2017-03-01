from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from rest_framework.fields import empty

from django_alt.abstract.validators import Validator
from django_alt.utils.shortcuts import coal


class BaseValidatedSerializer(serializers.Serializer):
    """
    Defines a relation between rest_framework serializer and validator
    """
    FIELD_VALIDATOR_PREFIX = 'field_'

    def __init__(self, instance=None, data=empty, *, validator_class=None, **kwargs):
        if not hasattr(self, 'Meta'):
            self.Meta = type('Meta', tuple(), dict())
        if validator_class:
            self.Meta.validator_class = validator_class

        assert hasattr(self.Meta, 'validator_class'), (
            'Either a `validator_class` set on the serializer Meta or '
            'provided when initializing the serializer is required.'
            'Offending serializer: {0}'
        ).format(self.__class__.__qualname__)

        self.permission_test = kwargs.pop('permission_test', None)
        self.did_check_permission = False

        self.Meta.validator_instance = self._instantiate_validator(**kwargs)
        super().__init__(instance, data, **kwargs)

    def _instantiate_validator(self, **kwargs):
        """
        Annotate the serializer with an instantiated model validator class
        :return: None
        """
        return self.Meta.validator_class(serializer=self, **kwargs)

    @staticmethod
    def _check_permissions(permission_test, attrs):
        try:
            if permission_test is not True and permission_test is not None and not permission_test(attrs):
                raise PermissionError()
        except (ObjectDoesNotExist, KeyError):
            raise PermissionError()
        return True

    @property
    def validator(self) -> Validator:
        """
        Fetches the validator instance bound to the serializer.
        The implementation of this behaviour varies for different
        serializer subclasses.
        :return: validator instance
        """
        return self.Meta.validator_instance

    @property
    def is_update(self) -> bool:
        """
        Helper method that checks if the serializer was initialized
        with an instance attribute to update
        :return: {bool}
        """
        return hasattr(self, 'instance') and self.instance is not None

    def validate_extras(self, attrs: dict):
        """
        If subclass defines functions named field_<field_name>
        where field_name corresponds to a field declared on the
        serializer, executes such functions with the field's value
        as the parameter.
        If subclass defines functions with names starting with check_,
        executes such functions with attrs dict as the parameter.
        All functions are called in alphabetical order.
        :return: None
        """
        fields = sorted(self.fields.fields.keys())
        for field in fields:
            name = self.FIELD_VALIDATOR_PREFIX + field
            if hasattr(self.validator, name) and callable(getattr(self.validator, name)) and field in attrs:
                getattr(self.validator, name)(attrs[field])

        self.validator.validate_checks(attrs)

    def check_permissions(self, attrs):
        """
        Performs post-permission checking, if a `permission_test` callable
        was passed to the serializer via its constructor
        :return: None
        :raises: PermissionError
        """
        self.permission_test is not None and self._check_permissions(self.permission_test, attrs)

    def validate(self, attrs: dict) -> dict:
        """
        Performs attribute validation before passing them to
        model managers.
        :param attrs: a dictionary containing input attributes to validate
        :return: transformed (if necessary) attributes from input
        """
        attrs = coal(self.validator.clean(attrs), attrs)
        attrs = coal(self.validator.base(attrs), attrs)

        self.validate_extras(attrs)

        if not self.is_update:
            attrs = coal(self.validator.will_create(attrs), attrs)
        else:
            attrs = coal(self.validator.will_update(self.instance, attrs), attrs)

        attrs = coal(self.validator.base_db(attrs), attrs)

        self.check_permissions(attrs)

        return attrs

    def to_representation(self, instance) -> OrderedDict:
        representation = super().to_representation(instance)
        result = self.validator.to_representation(representation,
                                                  self.validated_data if hasattr(self, '_validated_data') else None)
        return result if result else representation
