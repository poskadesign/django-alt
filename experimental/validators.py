from abc import abstractmethod

from django.db.models import Model, QuerySet
from typing import Type

from experimental.dotdict import ddict


class BaseLifecycleHooks:
    """
    Provides an interface to handle object lifecycle.
    """

    """
    Precursor lifecycle hooks.
    Invoked before a database operation
    """

    @abstractmethod
    def will_create(self):
        """
        Called when a new instance is created from attrs.
        Use this for
        - placing validation logic that should be solely executed on record creation
        :return: modified attrs
        """
        pass

    @abstractmethod
    def will_read(self, instance: Type[Model]):
        pass

    @abstractmethod
    def will_update(self, instance: Type[Model]):
        """
        Called when an existing instance is populated with new attrs.
        Use this for
        - placing validation logic that should be solely executed on record update
        :param instance: existing instance that will be updated
        :return: modified attrs
        """
        pass

    @abstractmethod
    def will_delete(self, queryset: Type[Model]):
        """
        Called before a queryset is deleted
        :param queryset: items to be deleted
        """
        pass

    """
    Postcursor lifecycle hooks.
    Invoked after a database operation
    """

    @abstractmethod
    def did_create(self, instance: Type[Model]):
        """
        Called after a model instance is created
        :param instance: the created model instance
        :return: None
        """
        pass

    @abstractmethod
    def did_update(self, instance: Type[Model]):
        """
        Called after a model instance is updated
        :param instance: the updated model instance
        :return: None
        """
        pass

    @abstractmethod
    def did_delete(self, queryset: Type[QuerySet]):
        """
        Called after a model instance is deleted
        :param queryset: queryset that was deleted
        :return: None
        """
        pass


class Validator(BaseLifecycleHooks):
    """
    Abstract class that defines the basic lifecycle hooks and definition
    principles for its subclasses
    """
    ATTR_CHECKS_PREFIX = 'check_'

    FIELD_CLEAN_PREFIX = 'clean_'
    FIELD_VALIDATOR_PREFIX = 'field_'
    FIELD_READ_PREP_PREFIX = 'read_'

    def __init__(self, attrs, *, model=None, context=None, **kwargs):
        """
        :param [model]: model class of the serialized object (if serialized by a ModelSerializer)
        :param [context]: any data that gets passed as serializer kwargs
        """
        self._attrs = ddict(attrs)
        self.model = model
        self.context = context

        self._is_create = kwargs.get('is_create', None)

    @property
    def is_create(self) -> bool:
        """
        Returns whether the currently validated operation is a part of resource creation.
        :return: is creation validated
        """
        assert self._is_create is not None, (
            '`is_create` flag was not passed when initializing the Validator\n'
            'but `is_create` or `is_update` accessor was invoked. Offending validator: `{}`.'
        ).format(self.__class__.__name__)
        return self._is_create

    @property
    def is_update(self) -> bool:
        """
        Returns whether the currently validated operation is a part of existing resource update.
        :return: is update validated
        """
        return not self.is_create

    @property
    def attrs(self) -> ddict:
        return self._attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs = ddict(value)

    def validate_checks(self):
        """
        If subclass defines functions with names starting with check_,
        executes such functions with attrs dict as the parameter.
        All functions are called in alphabetical order.
        """
        def is_attr_action(n):
            return n.startswith(self.ATTR_CHECKS_PREFIX) and callable(getattr(self, n))
        for name in (name for name in dir(self) if is_attr_action(name)):
            getattr(self, name)()

    def validate_fields(self):
        """
        If subclass defines functions named field_<field_name>
        where field_name corresponds to a field declared on the
        serializer, executes such functions with the field's value
        as the parameter.
        :return: None
        """
        for field in sorted(self.attrs.keys()):
            name = ''.join((self.FIELD_VALIDATOR_PREFIX, field))
            if hasattr(self, name) and callable(getattr(self, name)):
                getattr(self, name)(self.attrs[field])

    def clean_fields(self):
        """
        If subclass defines functions named clean_<field_name>
        where field_name corresponds to a attribute present in the attrs
        dict, executes such functions with the attribute's value
        as the parameter and sets the return value on the attrs dict
        :return: None
        """
        for field in sorted(self.attrs.keys()):
            name = ''.join((self.FIELD_CLEAN_PREFIX, field))
            if hasattr(self, name) and callable(getattr(self, name)):
                self.attrs[field] = getattr(self, name)(self.attrs[field])

    def prepare_read_fields(self, instance):
        """
        If subclass defines functions named read_<field_name>
        where field_name corresponds to a field declared on the
        serializer, executes such functions with the field's 
        representation value and read instance as the parameter.
        Such functions are expected to returned the prepared value
        that is written to the representation dict.
        :return: None
        """
        for field in sorted(self.attrs.keys()):
            name = ''.join((self.FIELD_READ_PREP_PREFIX, field))
            if hasattr(self, name) and callable(getattr(self, name)):
                self.attrs[field] = getattr(self, name)(self.attrs[field], instance)

    @abstractmethod
    def clean(self):
        """
        Base clean method. Executed before base validation.
        Use this for
        - value cleaning (lowercasing, normalization, etc.)
        - setting or generating default dependent values (like slugs)
        :return: modified attrs
        """
        pass

    @abstractmethod
    def base(self):
        """
        Executed before create and update methods.
        Use this for
        - raising validation errors independent from create or update
        :return: modified attrs
        """
        pass

    @abstractmethod
    def base_db(self):
        """
        Executed as last step of validation. As DB access can be considered
        expensive, this will run last, provided any other steps check out.
        Use this for
        - validation that requires database access
        - validation logic that is more expensive
        :return: modified attrs
        """
        pass
