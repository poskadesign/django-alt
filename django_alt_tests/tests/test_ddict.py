from unittest import TestCase

from django_alt.dotdict import ddict, undefined


class DdictTests(TestCase):
    def test_construction_from_dict(self):
        d = ddict({'a': 1, 'b': 2})
        self.assertEqual(len(d), 2)
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)

    def test_construction_from_ddict(self):
        d = ddict(ddict({'a': 1, 'b': 2}))
        self.assertEqual(len(d), 2)
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)

    def test_construction_from_iterable(self):
        d = ddict({'a': 1, 'b': 2}.items())
        self.assertEqual(len(d), 2)
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)

    def test_construction_from_kwargs(self):
        d = ddict(a=1, b=2)
        self.assertEqual(len(d), 2)
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)

    def test_construction_from_dict_and_kwargs(self):
        d = ddict({'c': 3}, a=1, b=2)
        self.assertEqual(len(d), 3)
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d.c, 3)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        self.assertEqual(d['c'], 3)

    def test_construction_from_iterable_and_kwargs(self):
        d = ddict((('c', 3),), a=1, b=2)
        self.assertEqual(len(d), 3)
        self.assertEqual(d.a, 1)
        self.assertEqual(d.b, 2)
        self.assertEqual(d.c, 3)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        self.assertEqual(d['c'], 3)

    def test_del(self):
        d = ddict(a=1, b=2)
        self.assertEqual(len(d), 2)
        del d.a
        self.assertEqual(len(d), 1)
        del d['b']
        self.assertEqual(len(d), 0)

    def test_nonexistent_key(self):
        d = ddict(a=1)
        self.assertTrue(d.b is undefined)

    def test_iter(self):
        result = {}
        for k, v in ddict(a=1, b=2):
            result[k] = v

        self.assertDictEqual(result, {'a': 1, 'b': 2})

        result = {}
        for k, v in ddict(a=1, b=2).items():
            result[k] = v

        self.assertDictEqual(result, {'a': 1, 'b': 2})

    def test_equality(self):
        a, b = ddict(a=1, b=2), dict(a=1, b=2)
        self.assertTrue(a == b)
        self.assertEqual(a, b)
        self.assertEqual(a, b)

        a, b = ddict(b=2, a=1), dict(a=1, b=2)
        self.assertTrue(a == b)
        self.assertEqual(a, b)
        self.assertEqual(a, b)

        a, b = ddict(b=2, a=1, c=3), dict(a=1, b=2)
        self.assertTrue(a != b)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, b)

        a, b = ddict(b=2, a=3), dict(a=1, b=2)
        self.assertTrue(a != b)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, b)

    def test_add_operator(self):
        a, b = ddict(b=2, a=1, c=3), dict(a=2, b=3)
        with self.assertRaises(TypeError):
            c = a + 1

        c = a + b
        self.assertDictEqual(c, dict(a=2, b=3, c=3))

        b2 = dict(z=4)
        c = a + b2
        self.assertDictEqual(a, dict(a=1, b=2, c=3))
        self.assertDictEqual(b2, dict(z=4))
        self.assertDictEqual(c, dict(a=1, b=2, c=3, z=4))

    def test_set_attribute(self):
        a = ddict()
        a.foo = 42
        self.assertEqual(dict(a)['foo'], 42)


class UndefinedTests(TestCase):
    def test_undefined_is_undefined(self):
        self.assertTrue(undefined is undefined)
        self.assertFalse(undefined is False)
        self.assertFalse(undefined is True)
        self.assertFalse(undefined is 1)
        self.assertFalse(undefined is 0)
        a = undefined
        self.assertTrue(a is undefined)

    def test_cannot_construct_undefined(self):
        with self.assertRaises(TypeError):
            undefined()

    def test_undefined_casts_to_false(self):
        self.assertFalse(bool(undefined))
        self.assertFalse(undefined)
