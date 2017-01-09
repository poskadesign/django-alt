from collections import OrderedDict

from rest_framework import serializers
from rest_framework.fields import empty

from django_alt.abstract.validators import BaseValidator


class BaseValidatedSerializer(serializers.Serializer):
    """
       Defines a relation between rest_framework serializer and validator
    """

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

        self.Meta.validator_instance = self._instantiate_validator(**kwargs)
        super().__init__(instance, data, **kwargs)

    def _instantiate_validator(self, **kwargs):
        """
        Annotate the serializer with an instantiated model validator class
        :return: None
        """
        return self.Meta.validator_class(**kwargs)

    @property
    def validator(self) -> BaseValidator:
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

    def validate(self, attrs: dict) -> dict:
        """
        Performs attribute validation before passing them to
        model managers.
        :param attrs: a dictionary containing input attributes to validate
        :return: transformed (if necessary) attributes from input
        """
        self.validator.clean(attrs)
        self.validator.base(attrs)

        if not self.is_update:
            self.validator.will_create(attrs)
        else:
            self.validator.will_update(self.instance, attrs)

        self.validator.base_db(attrs)

        if getattr(self.validator, 'permission_test', None) is not None:
            if not self.validator.permission_test(attrs):
                raise PermissionError()
        return attrs

    def to_representation(self, instance) -> OrderedDict:
        representation = super().to_representation(instance)
        return self.validator.to_representation(representation, self.validated_data)
