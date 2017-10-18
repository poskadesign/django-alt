import inspect
from abc import abstractmethod
from collections import OrderedDict

from typing import Type

from django.db.models import Model

from django_alt.dotdict import ddict, undefined


class Phasers:
    """
    Provides a standard interface for encapsulating code called during a specific validation phase.
    Inspired by Perl 6 phasers.
    """

    @abstractmethod
    def pre(self):
        """
        Function that is called before a validation sequence begins.
        Use this for
        - placing preconditional validation logic (`required` statements, etc.)
        Still, you should avoid using heavy validation logic here.
        """
        pass

    @abstractmethod
    def post(self):
        """
        Function that is called last after a full (successful) validation sequence.
        Use this for
        - placing extra cleanup code
        - code that should be executed after a validation sequence regardless whether an object
          was created/read/updated or deleted.
        """
        pass


class LifecycleHooks:
    """
    Provides a standard interface for handling object lifecycle.
    """

    """
    Precursor lifecycle hooks.
    Invoked before a database operation.
    """

    @abstractmethod
    def will_create(self):
        """
        Called when a new instance is created from attrs.
        Use this for
        - placing validation logic that should be solely executed on record creation
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
        """
        pass

    @abstractmethod
    def will_delete(self, instance: Type[Model]):
        """
        Called before a queryset is deleted
        :param instance: items to be deleted
        """
        pass

    @abstractmethod
    def will_create_or_update(self):
        """
        Called before an instance is created from or updated with attrs.
        """
        pass

    """
    Postcursor lifecycle hooks.
    Invoked after a database operation.
    """

    @abstractmethod
    def did_create(self, instance: Type[Model]):
        """
        Called after a model instance is created
        :param instance: the created model instance
        """
        pass

    @abstractmethod
    def did_update(self, instance: Type[Model]):
        """
        Called after a model instance is updated
        :param instance: the updated model instance
        """
        pass

    @abstractmethod
    def did_delete(self, instance: Type[Model]):
        """
        Called after a model instance is deleted
        :param instance: queryset that was deleted
        """
        pass

    @abstractmethod
    def did_create_or_update(self, instance: Type[Model]):
        """
        Called after a model instance is created or an existing instance updated
        :param instance: the created or updated model instance
        """
        pass


class Validator(LifecycleHooks, Phasers):
    """
    Abstract class that defines the basic lifecycle hooks and definition
    principles for its subclasses
    """
    ATTR_CHECKS_PREFIX = 'check_'

    FIELD_CLEAN_PREFIX = 'clean_'
    FIELD_DEFAULT_PREFIX = 'default_'
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
        return self._is_create

    @property
    def is_update(self) -> bool:
        """
        Returns whether the currently validated operation is a part of existing resource update.
        :return: is update validated
        """
        return (not self.is_create) if self.is_create is not None else None

    @property
    def attrs(self) -> ddict:
        return self._attrs

    @attrs.setter
    def attrs(self, value):
        if not isinstance(value, OrderedDict):
            self._attrs = ddict(value)
        else:
            self._attrs = value

    def validate_checks(self):
        """
        If subclass defines functions with names starting with check_,
        executes such functions with attrs dict as the parameter.
        All functions are called in alphabetical order.
        """

        def is_check(n):
            return n.startswith(self.ATTR_CHECKS_PREFIX) and callable(getattr(self, n))

        for name in (name for name in dir(self) if is_check(name)):
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

    def clean_and_default_fields(self):
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

        if self._is_create is not None and self._is_create is True:
            for default_func in (f for f in dir(self) if
                                 f.startswith(self.FIELD_DEFAULT_PREFIX) and callable(getattr(self, f))):
                field = default_func[len(self.FIELD_DEFAULT_PREFIX):]
                if field not in self.attrs:
                    self.attrs[field] = getattr(self, default_func)()

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
        read_funcs = ((name, method) for name, method in inspect.getmembers(self, predicate=inspect.ismethod) \
                      if name.startswith(self.FIELD_READ_PREP_PREFIX))
        for field, func in read_funcs:
            self.attrs[field[len(self.FIELD_READ_PREP_PREFIX):]] = func(self.attrs.get(field, undefined), instance)

    @abstractmethod
    def clean(self):
        """
        Base clean method. Executed before base validation.
        Use this for
        - value cleaning (lowercasing, normalization, etc.)
        - setting or generating default dependent values (like slugs)
        :return: None
        """
        pass

    @abstractmethod
    def base(self):
        """
        Executed before create and update methods.
        Use this for
        - raising validation errors independent from create or update
        :return: None
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
        :return: None
        """
        pass
