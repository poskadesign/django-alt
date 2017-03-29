from django_alt.abstract.validators import Validator
from django_alt.utils.shortcuts import coal


class ValidatedManager:
    """
    Relates validator to ObjectManager, allowing to easily use validator
    without needing a serializer
    """

    def __init__(self, model, validator_class: Validator, no_save=False, **context):
        self.model = model
        self.no_save = no_save
        self.validator = validator_class(model=model, serializer=None, **context)

    def validation_sequence(self, attrs: dict):
        self.validator.clean_fields(attrs, attrs.keys())

        attrs = coal(self.validator.clean(attrs), attrs)
        attrs = coal(self.validator.base(attrs), attrs)

        self.validator.validate_fields(attrs, attrs.keys())
        self.validator.validate_checks(attrs)

        attrs = coal(self.validator.will_create(attrs), attrs)
        attrs = coal(self.validator.base_db(attrs), attrs)

    def create(self, **attrs):
        """
        Validates and creates a model instance
        :param attrs: attributes to create the instance from.
        :return: the newly created instance
        """
        self.validation_sequence(attrs)

        if not self.no_save:
            instance = self.model.objects.create(**attrs)
            self.validator.did_create(instance, attrs)
            return instance

        return attrs

    def create_many(self, list_of_attrs):
        """
        TBA
        :param list_of_attrs:
        :return:
        """
        instances = []
        list_of_attrs = list(list_of_attrs)
        for attrs in list_of_attrs:
            self.validation_sequence(attrs)
            instances.append(self.model(**attrs))

        self.model.objects.bulk_create(instances)
        for instance, attrs in zip(instances, list_of_attrs):
            self.validator.did_create(instance, attrs)

        return instances
