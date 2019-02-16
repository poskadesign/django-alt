from unittest import TestCase

from django_alt.utils.iterables import recursive_key_map
from django_alt.utils.string import underscore_to_camelcase, camelcase_to_underscore


class UtilsIterablesTests(TestCase):
    def test_recursive_key_map_transforms_dict_correctly(self):
        input_1 = {'a': 42, 'b': 10}

        result = recursive_key_map(str.upper, input_1)
        self.assertDictEqual(result, {'A': 42, 'B': 10})

    def test_recursive_key_map_transforms_nested_dict_correctly(self):
        input_1 = {'a': {'b': 10, 'c': {'d': 42}}, 'b': 10}

        result = recursive_key_map(str.upper, input_1)
        self.assertDictEqual(result, {'A': {'B': 10, 'C': {'D': 42}}, 'B': 10})

    def test_recursive_key_map_transforms_list_of_dicts_correctly(self):
        input_1 = [{'a': 1}, {'b': 2}]

        result = recursive_key_map(str.upper, input_1)
        self.assertListEqual(result, [{'A': 1}, {'B': 2}])

    def test_recursive_key_map_transforms_nested_list_of_dicts_correctly(self):
        input_1 = [{'a': 1}, {'b': [{'c': [{'d': []}]}]}]

        result = recursive_key_map(str.upper, input_1)
        self.assertListEqual(result, [{'A': 1}, {'B': [{'C': [{'D': []}]}]}])


class UtilsStringTests(TestCase):
    def test_underscore_to_camelcase(self):
        self.assertEqual(underscore_to_camelcase('first_name'), 'firstName')
        self.assertEqual(underscore_to_camelcase('underscore_to_camelcase'), 'underscoreToCamelcase')
        self.assertEqual(underscore_to_camelcase('long__string'), 'long_String')
        self.assertEqual(underscore_to_camelcase('search_tags_1'), 'searchTags1')

    def test_camelcase_to_underscore(self):
        self.assertEqual(camelcase_to_underscore('firstName'), 'first_name')
        self.assertEqual(camelcase_to_underscore('underscoreToCamelcase'), 'underscore_to_camelcase')
        self.assertEqual(camelcase_to_underscore('long_String'), 'long_string')
        self.assertEqual(camelcase_to_underscore('searchTags1'), 'search_tags_1')
