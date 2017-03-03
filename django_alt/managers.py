from django_alt.abstract.validators import Validator
from django_alt.utils.shortcuts import coal


class ValidatedManager:
    """
    Relates validator to ObjectManager, allowing to easily use validator
    without needing a serializer
    """

    def __init__(self, model, validator_class: Validator, **context):
        self.model = model
        self.validator = validator_class(model=model, serializer=None, **context)

    def _validate_extras(self, attrs: dict):
        for field in sorted(attrs.keys()):
            name = Validator.FIELD_VALIDATOR_PREFIX + field
            if hasattr(self.validator, name) and callable(getattr(self.validator, name)) and field in attrs:
                getattr(self.validator, name)(attrs[field])

        self.validator.validate_checks(attrs)

    def create(self, **attrs):
        """
        Validates and creates a model instance
        :param attrs: attributes to create the instance from.
        :return: the newly created instance
        """
        attrs = coal(self.validator.clean(attrs), attrs)
        attrs = coal(self.validator.base(attrs), attrs)

        self._validate_extras(attrs)

        attrs = coal(self.validator.will_create(attrs), attrs)
        attrs = coal(self.validator.base_db(attrs), attrs)

        instance = self.model.objects.create(**attrs)
        self.validator.did_create(instance, attrs)

        return instance
