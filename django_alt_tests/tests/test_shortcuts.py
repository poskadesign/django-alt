from unittest import TestCase

from django_alt.utils.shortcuts import *


class UtilsShortcutsTests(TestCase):
    def test_make_error(self):
        self.assertEqual(make_error('k', 'v'), {'k': ['v.']})
        self.assertEqual(make_error('k', 'v.'), {'k': ['v.']})
        self.assertEqual(make_error(['k'], 'v'), {'k': ['v.']})
        self.assertEqual(make_error(['k'], ['v']), {'k': ['v.']})
        self.assertEqual(make_error(['k1', 'k2'], ['v']), {'k1': ['v.'], 'k2': ['v.']})
        self.assertEqual(make_error(['k1', 'k2'], ['v1', 'v2']), {'k1': ['v1.', 'v2.'], 'k2': ['v1.', 'v2.']})
        self.assertEqual(make_error(None, 'v1'), {'non_field_errors': ['v1.']})

    def test_invalid(self):
        with self.assertRaises(validation_error_class) as ex:
            invalid('k', 'v')
        self.assertEqual(ex.exception.detail, {'k': ['v.']})

    def test_invalid_if(self):
        invalid_if(False, 'k', 'v')
        with self.assertRaises(validation_error_class) as ex:
            invalid_if(True, 'k', 'v')
        self.assertEqual(ex.exception.detail, {'k': ['v.']})

    def test_coal(self):
        self.assertDictEqual(coal(None, {}), {})
        self.assertDictEqual(coal(None, {'a': 5}), {'a': 5})
        self.assertEqual(coal(1, {'a': 5}), 1)
        self.assertEqual(coal(False, {'a': 5}), False)
        self.assertEqual(coal(False, None), False)
        self.assertEqual(coal(None, False), False)
        self.assertEqual(coal(None, None), None)

    def test_if_in(self):
        a = dict(a=1, b=2)
        self.assertTrue(if_in('a', a, lambda a: a + 1))
        self.assertEqual(a['a'], 2)
        self.assertFalse(if_in('c', a, lambda c: c + 1, 15))
        self.assertEqual(a['c'], 15)

    def test_first_defined(self):
        self.assertEqual(first_defined(
            False
        ), False)

        self.assertEqual(first_defined(
            None,
            False
        ), False)

        self.assertEqual(first_defined(
            None,
            False,
            'foo',
        ), False)

    def test_if_all_in(self):
        a = dict(a=1, b=2, c=3)
        self.assertTrue(if_all_in(['a', 'b', 'c'], a, lambda v: v + 1))
        self.assertDictEqual(a, dict(a=2, b=3, c=4))

        self.assertFalse(if_all_in(['a', 'b', 'c', 'foo'], a, lambda v: v + 1))
        self.assertDictEqual(a, dict(a=2, b=3, c=4))

        self.assertTrue(if_all_in(['a', 'b'], a, lambda v: v + 1))
        self.assertDictEqual(a, dict(a=3, b=4, c=4))

    def test_if_any_in(self):
        a = dict(a=1, b=2, c=3)
        self.assertTrue(if_any_in(['a', 'b', 'c'], a, lambda v: v + 1))
        self.assertDictEqual(a, dict(a=2, b=3, c=4))

        self.assertTrue(if_any_in(['z', '45', 'a', 'b', 'c', 'foo'], a, lambda v: v + 1))
        self.assertDictEqual(a, dict(a=3, b=4, c=5))

        self.assertTrue(if_any_in(['a', 'b'], a, lambda v: v + 1))
        self.assertDictEqual(a, dict(a=4, b=5, c=5))

        self.assertFalse(if_any_in(['x', 'y'], a, lambda v: v + 1))
        self.assertDictEqual(a, dict(a=4, b=5, c=5))

    def test_try_cast(self):
        self.assertEqual(try_cast(int, '5'), 5)
        self.assertEqual(try_cast(float, '5.15'), 5.15)
        self.assertEqual(try_cast(float, '5.A15'), None)