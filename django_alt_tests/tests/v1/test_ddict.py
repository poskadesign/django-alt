from django.test import TestCase

from experimental.dotdict import ddict


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

    def test_key_error(self):
        d = ddict(a=1)
        with self.assertRaises(KeyError):
            d.b

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
