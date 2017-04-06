from itertools import chain


class ddict(dict):
    def __init__(self, iterable=None, **kwargs):
        if iterable is not None:
            if isinstance(iterable, dict):
                iterable.update(kwargs)
            else:
                iterable = chain(iterable, kwargs.items())
            super().__init__(iterable)
        else:
            super().__init__(**kwargs)

    def __iter__(self):
        return self.items().__iter__()

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

