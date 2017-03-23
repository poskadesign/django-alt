import collections

from django.db.models import QuerySet
from rest_framework import serializers

validation_error_class = serializers.ValidationError


def invalid_if(condition, key_or_list, error_or_list):
    """
    Shortcut for raising a validation error if a condition is met.
    :raises: serializers.ValidationError
    """
    if condition:
        invalid(key_or_list, error_or_list)


def invalid(key_or_list, error_or_list):
    """
    Shortcut for raising a validation error.
    :raises: serializers.ValidationError
    """
    raise validation_error_class(make_error(key_or_list, error_or_list))


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
    return isinstance(queryset, QuerySet) or hasattr(queryset, '__iter__')


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
    :param args: arguments to check for "defineness"
    :return:
    """
    for arg in args:
        if arg is not None:
            return arg
    return None


def try_cast(typ, value):
    """
    Attempts to cast value to a given type.
    :param typ: type to cast to
    :param value: value to be casted
    :return: casted value if cast was successful, otherwise None
    """
    try:
        return typ(value)
    except ValueError:
        return None
