import inspect
from abc import abstractmethod
from collections import OrderedDict


class Validator:
    """
    Abstract class that defines the basic lifecycle hooks and definition
    principles for its subclasses
    """
    ATTR_CHECKS_PREFIX = 'check_'

    FIELD_CLEAN_PREFIX = 'clean_'
    FIELD_VALIDATOR_PREFIX = 'field_'

    def __init__(self, *, model=None, serializer=None, **context):
        """
        :param [model]: model class of the serialized object (if serialized by a ModelSerializer)
        :param [context]: any data that gets passed as serializer kwargs
        """
        self.model = model
        self.serializer = serializer
        self.context = context

    def validate_checks(self, attrs):
        """
        If subclass defines functions with names starting with check_,
        executes such functions with attrs dict as the parameter.
        All functions are called in alphabetical order.
        :param attrs: attrs dict to pass as parameter
        """
        def is_attr_action(name):
            return name.startswith(self.ATTR_CHECKS_PREFIX) and callable(getattr(self, name))
        for name in [name for name in dir(self) if is_attr_action(name)]:
            getattr(self, name)(attrs)

    def validate_fields(self, attrs, field_names):
        """
        If subclass defines functions named field_<field_name>
        where field_name corresponds to a field declared on the
        serializer, executes such functions with the field's value
        as the parameter.
        :param attrs: attrs to check
        :param field_names: an iterable of fields defined by name
        :return: None
        """
        for field in sorted(field_names):
            name = ''.join((self.FIELD_VALIDATOR_PREFIX, field))
            if hasattr(self, name) and callable(getattr(self, name)) and field in attrs:
                func = getattr(self, name)
                if len(inspect.getfullargspec(func).args) == 3:
                    # field_<>(self, value, attrs)
                    getattr(self, name)(attrs[field], attrs)
                else:
                    # field_<>(self, value)
                    getattr(self, name)(attrs[field])

    def clean_fields(self, attrs, field_names):
        """
        If subclass defines functions named clean_<field_name>
        where field_name corresponds to a field declared on the
        serializer, executes such functions with the field's value
        as the parameter and sets the return value on the attrs dict
        :param attrs: dict to apply the cleaned values on
        :param field_names: an iterable of fields defined by name
        :return: cleaned value
        """
        for field in sorted(field_names):
            name = ''.join((self.FIELD_CLEAN_PREFIX, field))
            if hasattr(self, name) and callable(getattr(self, name)) and field in attrs:
                attrs[field] = getattr(self, name)(attrs[field])

    @abstractmethod
    def clean(self, attrs: dict) -> dict:
        """
        Base clean method. Executed before base validation.
        Use this for
        - value cleaning (lowercasing, normalization, etc.)
        - setting or generating default dependent values (like slugs)
        :param attrs: dict containing model object attribute values
        :return: modified attrs
        """
        return attrs

    @abstractmethod
    def base(self, attrs: dict) -> dict:
        """
        Executed before create and update methods.
        Use this for
        - raising validation errors independent from create or update
        :param attrs: dict containing model object attribute values
        :return: modified attrs
        """
        return attrs

    @abstractmethod
    def base_db(self, attrs: dict) -> dict:
        """
        Executed as last step of validation. As DB access can be considered
        expensive, this will run last, provided any other steps check out.
        Use this for
        - validation that requires database access
        - validation logic that is more expensive
        :param attrs: dict containing model object attribute values
        :return: modified attrs
        """
        return attrs

    @abstractmethod
    def will_create(self, attrs: dict) -> dict:
        """
        Called when a new instance is created from attrs.
        Use this for
        - placing validation logic that should be solely executed on record creation
        :param attrs: attrs to create the instance
        :return: modified attrs
        """
        return attrs

    @abstractmethod
    def will_update(self, instance, attrs: dict) -> dict:
        """
        Called when an existing instance is populated with new attrs.
        Use this for
        - placing validation logic that should be solely executed on record update
        :param instance: existing instance
        :param attrs: attrs to update the instance with
        :return: modified attrs
        """
        return attrs

    @abstractmethod
    def will_delete(self, queryset):
        """
        Called before a queryset is deleted
        :param queryset: items to be deleted
        """
        pass

    @abstractmethod
    def did_create(self, instance, validated_attrs: dict) -> None:
        """
        Called after a model instance is created
        :param instance: the created model instance
        :param validated_attrs: validated attrs used to create the instance
        :return: None
        """
        pass

    @abstractmethod
    def did_update(self, instance, validated_attrs: dict) -> None:
        """
        Called after a model instance is updated
        :param instance: the updated model instance
        :param validated_attrs: validated attrs used to update the instance
        :return: None
        """
        pass

    @abstractmethod
    def did_delete(self) -> None:
        """
        Called after a model instance is deleted
        :return: None
        """
        pass

    @abstractmethod
    def to_representation(self, repr_attrs: OrderedDict, validated_attrs: dict = None) -> OrderedDict:
        """
        Called when a queried object is transformed to a dict of primitives by underlying DRF.
        Use this for
        - post-processing display values before converting them to JSON
        :param repr_attrs: an OrderedDict that is composed by DRF
        :param validated_attrs: a dict containing attributes that were passed through validation functions
        :return: modified repr_attrs OrderedDict
        """
        return repr_attrs
