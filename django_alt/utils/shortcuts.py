from rest_framework import serializers

validation_error_class = serializers.ValidationError


def invalid_if(condition, key_or_list, error_or_list):
    """
    shortcut for raising a validation error if a condition is met
    :raises: serializers.ValidationError
    """
    if condition:
        invalid(key_or_list, error_or_list)


def invalid(key_or_list, error_or_list):
    """
    shortcut for raising a validation error
    :raises: serializers.ValidationError
    """
    raise validation_error_class(make_error(key_or_list, error_or_list))


def make_error(key_or_list, error_or_list) -> dict:
    """
    creates a unified error object
    :param key_or_list: field name (can be None if error is a non_field one or a list of str)
    :param error_or_list: one or more string representations of the error
    """
    err = error_or_list if isinstance(error_or_list, list) else [error_or_list]
    err = list(map(lambda e: (e if e[-1] == '.' else e + '.') if len(e) else e, err))
    if key_or_list:
        return {k: err for k in key_or_list} if isinstance(key_or_list, list) else {key_or_list: err}
    return {'non_field_errors': err}


def if_in(key, container, func_true=None, func_false=None):
    """
    checks if given key on the container exists and executes
    func_true or func_false with each corresponding value based on the outcome
    :param key: the key to search
    :param container: the container to search in
    :param func_true: callable that is called on success: func_true(container[key])
    :param func_false: callable that is called on fail: func_false(container[key])
    :return: whether the key exists
    """
    if key in container and func_true is not None:
        container[key] = func_true(container[key])
        return True
    elif func_false is not None:
        container[key] = func_false()
        return False
