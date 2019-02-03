from collections import Iterable


def recursive_key_map(mapping_func, iterable):
    """
    Recursively iterates through lists and dictionaries and applies
    a mapping function to keys in found dictionaries.
    Does not mutate the original variable.
    :param mapping_func: mapping function that takes a string and returns a string
    :param iterable: the iterable that mapping should be applied to
    :return: a new iterable with applied transformations
    """
    if isinstance(iterable, dict):
        new_dict = {}
        for key, value in iterable.items():
            if isinstance(key, str):
                key = mapping_func(key)
            new_dict[key] = recursive_key_map(mapping_func, value)
        return new_dict
    if not isinstance(iterable, str) and isinstance(iterable, Iterable):
        return [recursive_key_map(mapping_func, value) for value in iterable]
    else:
        return iterable
