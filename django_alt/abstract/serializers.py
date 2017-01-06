from abc import abstractmethod, abstractproperty


class BaseValidatedSerializer:
    """
       Defines a relation between rest_framework serializer and validator
   """

    @abstractmethod
    def _instantiate_validator(self, **kwargs):
        """
        Annotate the serializer with an instantiated model validator class
        :return: None
        """
        pass

    @abstractproperty
    def validator_instance(self):
        """
        Fetches the validator instance bound to the serializer.
        The implementation of this behaviour varies for different
        serializer subclasses.
        :return: validator instance
        """
        pass

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
        validator = self.Meta.validator_instance

        validator.clean(attrs)
        validator.base(attrs)

        if not self.is_update:
            validator.will_create(attrs)
        else:
            validator.will_update(self.instance, attrs)

        validator.base_db(attrs)

        if getattr(validator, 'permission_test', None) is not None:
            if not validator.permission_test(attrs):
                raise PermissionError()

        return attrs
