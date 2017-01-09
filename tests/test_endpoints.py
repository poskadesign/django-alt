from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from django_alt.abstract.endpoints import MetaEndpoint
from django_alt.endpoints import Endpoint
from tests.conf.endpoints import ModelASerializer, ModelAEndpoint1
from tests.conf.models import ModelA


class MetaEndpointTests(TestCase):
    def test_transform_config(self):
        def are_equal(c1, c0):
            c1 = MetaEndpoint.transform_config(c1)
            self.assertDictEqual(c0, c1)

        are_equal({
            'get': None
        }, {
            'get': {}
        })

        are_equal({
            'get, post': None
        }, {
            'get': {},
            'post': {}
        })

        are_equal({
            ' get,post, put': None
        }, {
            'get': {},
            'post': {},
            'put': {},
        })
        are_equal({
            ' get,post': {
                'q': 1
            }
        }, {
            'get': {'q': 1},
            'post': {'q': 1},
        })
        are_equal({
            ' get,post': {
                'q': 1
            },
            'post': {
                'z': 2
            }
        }, {
            'get': {'q': 1},
            'post': {'q': 1, 'z': 2},
        })
        are_equal({
            ' get': {
                'q': 1
            },
            'get': {
                'z': 2
            }
        }, {
            'get': {'q': 1, 'z': 2},
        })
        are_equal({
            ' get, get': {
                'q': 1
            },
            'post,get': {
                'z': 4
            }
        }, {
            'get': {'q': 1, 'z': 4},
            'post': {'z': 4}
        })

    def test_unknown_http_method(self):
        with self.assertRaises(AssertionError):
            class MyEndpoint(Endpoint):
                serializer = ModelASerializer
                config = {'get,foo': None}


class EndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_required_fields(self):
        with self.assertRaises(AssertionError):
            class MyEndpoint(Endpoint):
                pass

        with self.assertRaises(AssertionError):
            class MyEndpoint1(Endpoint):
                config = {
                    'foo': {
                        'query': None
                    }
                }

        with self.assertRaises(AssertionError):
            class MyEndpoint2(Endpoint):
                config = {
                    'get': {
                        'query': None
                    }
                }

        with self.assertRaises(AssertionError):
            class MyEndpoint3(Endpoint):
                config = {
                    'get': {
                        'filters': {
                            'y': lambda x, y: (x, y)
                        }
                    }}

        with self.assertRaises(AssertionError):
            class MyEndpoint4(Endpoint):
                config = {
                    'get': {
                        'query': lambda x, y: (x, y),
                        'filters': {
                            'x': lambda x, y: (x, y)
                        }
                    }}

        with self.assertRaises(AssertionError):
            class MyEndpoint5(Endpoint):
                serializer = ModelASerializer
                config = {
                    'get': {
                        'query': lambda x, y: (x, y),
                        'filters': lambda x, y: (x, y)
                    }}

        with self.assertRaises(AssertionError):
            class MyEndpoint7(Endpoint):
                serializer = ModelASerializer
                config = {
                    'get': {
                        'query': {'something_strange'},
                        'filters': {
                            'x': lambda x, y: (x, y)
                        }
                    }}

        with self.assertRaises(AssertionError):
            class MyEndpoint8(Endpoint):
                serializer = ModelASerializer
                config = {
                    'delete': None
                }

        class MyEndpoint6(Endpoint):
            serializer = ModelASerializer
            config = {
                'get': {
                    'query': lambda x, y: (x, y),
                    'filters': {
                        'x': lambda x, y: (x, y)
                    }
                },
                'delete': {
                    'query': lambda x, y: (x, y)
                }}

    def test_basic_get(self):
        self.assertTrue(hasattr(ModelAEndpoint1, 'as_view'))
        resp = self.client.get(reverse('e1'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])

        ModelA.objects.create(field_1='aa', field_2=5)
        resp = self.client.get(reverse('e1'))
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(dict(resp.data[0]), {'id': 1, 'field_1': 'aa', 'field_2': 5})

    def test_raises_validation_error(self):
        ModelA.objects.create(field_1='aa', field_2=5)
        resp = self.client.get(reverse('e2'))
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(dict(resp.data[0]), {'id': 1, 'field_1': 'aa', 'field_2': 5, 'extra': 'this is an extra'})

        ModelA.objects.create(field_1='aa', field_2=5)
        resp = self.client.get(reverse('e2'))
        self.assertEqual(resp.status_code, 400)
        self.assertDictEqual(dict(resp.data), {'error': ['msg.']})

    def test_filtered_get(self):
        ModelA.objects.create(field_1='aaa', field_2=5)
        ModelA.objects.create(field_1='aaa', field_2=6)
        ModelA.objects.create(field_1='aca', field_2=10)
        ModelA.objects.create(field_1='ada', field_2=10)
        ModelA.objects.create(field_1='aea', field_2=10)
        ModelA.objects.create(field_1='aaa', field_2=10)

        resp = self.client.get(reverse('e3') + '?filter1=aaa')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 3)
        for d in resp.data:
            self.assertEqual(d['field_1'], 'aaa')

        resp = self.client.get(reverse('e3') + '?filter2=10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 4)
        for d in resp.data:
            self.assertEqual(d['field_2'], 10)

        resp = self.client.get(reverse('e3') + '?filter1=aaa&filter2=10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        for d in resp.data:
            self.assertEqual(d['field_1'], 'aaa')
            self.assertEqual(d['field_2'], 10)

    def test_get_precondition_permission_check(self):
        resp = self.client.get(reverse('e4'))
        self.assertEqual(resp.status_code, 401)

    def test_get_postcondition_permission_check(self):
        resp = self.client.get(reverse('e5'))
        self.assertEqual(resp.status_code, 401)
