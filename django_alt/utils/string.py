import re

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


def underscore_to_camelcase(value):
    def camelcase():
        yield str.lower
        while True:
            yield str.capitalize

    c = camelcase()
    return ''.join(next(c)(x) if x else '_' for x in value.split('_'))


def camelcase_to_underscore(value):
    s1 = _first_cap_re.sub(r'\1_\2', value)
    return _all_cap_re.sub(r'\1_\2', s1).lower()
