import collections
from typing import Union

from django.db.models import QuerySet
from rest_framework import serializers

ValidationError = serializers.ValidationError


def as_bool(string: str) -> Union[bool, None]:
    """
    Shortcut for checking if string is actually a representation for bool.
    This is useful when i.e. passing bool values by query string.
    :param string: input to check
    :return: bool value if string matches, None otherwise
    """
    lower = string.lower()
    if lower == 'true':
        return True
    elif lower == 'false':
        return False
    return None


def copyattrs(source, destination, *attrs):
    """
    Shortcut for getting multiple attributes from a source object and
    setting them on the destination object.
    Useful for when you want to set multiple ddict attributes on a class instance.
    :param source: object that will have getattr called on
    :param destination: object that will have setattr called on
    :param attrs: list of attributes to iterate on
    :return: destination object
    """
    for attr in attrs:
        setattr(destination, attr, getattr(source, attr))
    return destination


def invalid_if(condition, key_or_list, error_or_list):
    """
    Shortcut for raising a validation error if a condition is met.
    :raises: serializers.ValidationError
    """
    return not condition or invalid(key_or_list, error_or_list)


def invalid(key_or_list, error_or_list):
    """
    Shortcut for raising a validation error.
    :raises: serializers.ValidationError
    """
    raise ValidationError(make_error(key_or_list, error_or_list))


def is_iterable(obj):
    """
    Shortcut for checking if object is an iterable.
    This method *does not* count strings as iterables.
    :param obj: object to check
    :return: whether the object is an iterable or not
    """
    return not isinstance(obj, str) and isinstance(obj, collections.Iterable)


def make_error(key_or_list, error_or_list) -> dict:
    """
    Creates a unified error object.
    :param key_or_list: field name (can be None if error is a non_field one or a list of str)
    :param error_or_list: one or more string representations of the error
    """
    err = error_or_list if is_iterable(error_or_list) else [error_or_list]
    err = list(map(lambda e: (e if e[-1] == '.' or e[-1] == '!' else e + '.') if len(e) else e, err))
    if key_or_list:
        return {k: err for k in key_or_list} if is_iterable(key_or_list) else {key_or_list: err}
    return {'non_field_errors': err}


def if_in(key, container, func_true=None, default=None):
    """
    Checks if given key on the container exists and executes.
    func_true or func_false with each corresponding value based on the outcome.
    :param key: the key to search
    :param container: the container to search in
    :param func_true: callable that is called on success: func_true(container[key])
    :param default: default value to set if key does not exist in the container
    :return: {bool} whether the key exists
    """
    if key in container and func_true is not None:
        container[key] = func_true(container[key])
        return True
    elif default is not None:
        container[key] = default
        return False


def queryset_has_many(queryset) -> bool:
    """
    Checks whether a given query product is iterable.
    :param queryset: Django QuerySet object
    :return: {bool}
    """
    return isinstance(queryset, QuerySet) or is_iterable(queryset)


def coal(obj, fallback):
    """
    Inspired by C# null-coalescing operator:
    C# --> not_null = obj ?? new Object()
    Py --> not_null = coal(obj, Object())
    Also returns fallback upon a KeyError
    """
    try:
        return obj if obj is not None else fallback
    except KeyError:
        return fallback


def coald(obj, fallback_lambda):
    """
    A deferred variation of the null-coalescing operator.
    Returns obj if it is defined, execution result of a parametress lambda (fallback_lambda) otherwise.
    """
    return obj if obj is not None else fallback_lambda()


def if_all_in(keys, container, func_true=None):
    """
    checks if all given keys are in the container and
    executes func_true for each of the corresponding values
    :param keys: iterable of keys to find
    :param container: the container to search in
    :param func_true: callable that is called for each value on success: func_true(container[key])
    :return: whether the keys exist
    """
    if all(key in container for key in keys):
        for key in keys:
            container[key] = func_true(container[key])
        return True
    return False


def if_any_in(keys, container, func_true=None):
    """
    checks if any given keys ar in the container and
    executes func_true for each of the corresponding values of the existing keys
    :param keys: iterable of keys to find
    :param container: the container to search in
    :param func_true: callable that is called for each value on success: func_true(container[key])
    :return: whether any of the keys exist
    """
    found_key = False
    for key in keys:
        if key in container:
            container[key] = func_true(container[key])
            found_key = True
    return found_key


def first_defined(*args):
    """
    Finds the first argument that is not None
    :param args: arguments to check for "definedness"
    :return:
    """
    for arg in args:
        if arg is not None:
            return arg
    return None


def prohibited(key: str, container: dict = None):
    """
    shortcut for raising a validation error when a prohibited field is in the container.
    :param container: container to search
    :param key: existing key
    :raises: serializer.ValidationError
    """
    invalid_if(container and key in container, key, 'This field cannot be present.')


def prohibited_any(keys: tuple, container: dict = None):
    """
    shortcut for raising a validation error when any of the given fields exist in the container.
    :param keys: keys that cannot be in the container
    :param container: container to search
    :raises: serializer.ValidationError
    """
    if container:
        intersection = set(keys).intersection(container.keys())
        if len(intersection) > 0:
            invalid(intersection, 'This field cannot be present.')


def required(key: str, container: dict = None):
    """
    shortcut for raising a validation error about a missing required field.
    :param key: missing key
    :param container: container to search
    :raises: serializer.ValidationError
    """
    if container and key in container:
        return container[key]
    invalid(key, 'This field is required.')


def required_all(keys: list, container: dict = None):
    """
    shortcut for raising a validation error if any of the keys are missing in the container.
    :param keys: keys that are required in the container
    :param container: container to search
    :raises: serializer.ValidationError
    """
    if container:
        difference = set(keys).difference(container.keys())
        if len(difference):
            invalid(difference, 'This field is required.')


def try_cast(typ, value):
    """
    Attempts to cast value to a given type.
    :param typ: type to cast to
    :param value: value to be casted
    :return: casted value if cast was successful, otherwise None
    """
    try:
        return typ(value)
    except (ValueError, TypeError):
        return None


def valid_if(condition, key_or_list, error_or_list):
    """
    Shortcut for raising a validation error if a condition is not met.
    Think about this function as an assertion (i.e. this condition must be met).
    :raises: serializers.ValidationError
    :returns: the condition variable, if it is truthy
    """
    return condition or invalid(key_or_list, error_or_list)


"""
Alias of `valid_if`.
Used in Design by Contract methodology to denote
that a callable asserts that a given condition is true
before executing any code
"""
expects = valid_if

"""
Alias of `valid_if`.
Used in Design by Contract methodology to denote
that a callable asserts that a given condition is true
after its code block is executed
"""
ensures = valid_if
