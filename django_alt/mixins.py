from typing import Union

from django_alt.dotdict import ddict
from django_alt.utils.iterables import recursive_key_map
from django_alt.utils.string import underscore_to_camelcase, camelcase_to_underscore


class CamelcaseTransformMixin:
    def transform_input_data(self, data: Union[ddict, list]) -> Union[ddict, list, None]:
        return recursive_key_map(underscore_to_camelcase, data)

    def transform_output_data(self, data: Union[ddict, list]) -> Union[ddict, list, None]:
        return recursive_key_map(camelcase_to_underscore, data)
