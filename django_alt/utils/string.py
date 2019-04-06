import re

import inflection

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


def underscore_to_camelcase(value):
    return inflection.camelize(value, False)


def camelcase_to_underscore(value):
    return inflection.underscore(value)
