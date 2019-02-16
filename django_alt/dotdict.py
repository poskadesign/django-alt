from collections import OrderedDict
from itertools import chain


class _undefined_meta(type):
    def __bool__(self):
        return False


class undefined(metaclass=_undefined_meta):
    """
    An empty class that designates a non-existing ddict item.
    Used for graceful item retrieval.
    Inspired by JavaScript.
    """
    def __new__(cls, *args, **kwargs):
        if cls is undefined:
            raise TypeError('Class `undefined` cannot be instantiated')

    def __bool__(self):
        return False


class ddict(OrderedDict):
    def __init__(self, iterable=None, **kwargs):
        if iterable is not None:
            if isinstance(iterable, dict):
                iterable.update(kwargs)
            else:
                iterable = chain(iterable, kwargs.items())
            super().__init__(iterable)
        else:
            super().__init__(**kwargs)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = ddict(v)
            elif isinstance(v, list):
                for i, list_item in enumerate(v):
                    if isinstance(list_item, dict):
                        v[i] = ddict(list_item)


    def __iter__(self):
        return self.items().__iter__()

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            return undefined

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __add__(self, other):
        if isinstance(other, dict):
            result = self.copy()
            result.update(other)
            return result
        raise TypeError('You can only add two ddict or one ddict one dict instances')

