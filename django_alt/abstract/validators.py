from abc import abstractmethod
from collections import OrderedDict


class Validator:
    """
    Abstract class that defines the basic lifecycle hooks and definition
    principles for its subclasses
    """

    def __init__(self, *, model=None, serializer=None, **context):
        """
        :param [model]: model class of the serialized object (if serialized by a ModelSerializer)
        :param [context]: any data that gets passed as serializer kwargs
        """
        self.model = model
        self.serializer = serializer
        self.context = context

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
        Called after a model instance is created
        :param instance: the updated model instance
        :param validated_attrs: validated attrs used to update the instance
        :return: None
        """
        pass

    @abstractmethod
    def did_delete(self, attrs: dict) -> None:
        """
        Called after a model instance is deleted
        :param attrs: dict of data passed from the request object
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
        :param validated_attrs: an dict containing attributes that were passed through validation functions
        :return: modified attrs OrderedDict
        """
        return repr_attrs
