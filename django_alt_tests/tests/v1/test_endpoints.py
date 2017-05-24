import inspect

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from django_alt_tests.conf.models import ModelA
from experimental.endpoints import Endpoint, KW_CONFIG_URL_FIELDS, MetaEndpoint
from experimental.serializers import ValidatedSerializer


class ConcreteSerializer(ValidatedSerializer):
    class Meta:
        model = ModelA


class ConcreteEndpoint(Endpoint):
    serializer = ConcreteSerializer
    config = {
        'get': None
    }


class EndpointViewLogicTests(TestCase):
    def setUp(self):
        class EBase(Endpoint):
            serializer = ConcreteSerializer
            config = { 'get': None }
        self.EBase = EBase

    def patchE(self, method):
        self.EBase.on_get = method
        return self.EBase.as_view()(self.mock_request('GET'))

    def mock_request(self, method):
        return type('RequestMock', tuple(), dict(method=method))

    def test_should_return_405_for_nonexistent_method_positive(self):
        req = self.mock_request('POST')
        resp = ConcreteEndpoint.as_view()(req)
        self.assertEqual(resp.status_code, 405)

    def test_overridden_endpoint_handler_return_type_checks_negative(self):
        def on_get_1(self, context, **url):
            return None
        def on_get_2(self, context, **url):
            return 200
        def on_get_3(self, context, **url):
            return {'a', 'b'}
        def on_get_4(self, context, **url):
            return {'a': 'b'}
        def on_get_5(self, context, **url):
            return {'a': 'b'}, 200
        def on_get_6(self, context, **url):
            return Response({'a': 'b'}, 200)
        def on_get_7(self, context, **url):
            return {'a': 'b'}, 200, 'foo'
        def on_get_8(self, context, **url):
            return {'a': 'b'}, 'foo'

        for method in (on_get_1, on_get_2, on_get_3, on_get_7, on_get_8):
            with self.assertRaises(AssertionError):
                self.patchE(method)

        all((self.patchE(on_get_4), self.patchE(on_get_5), self.patchE(on_get_6)))

    def test_overridden_endpoint_handler_handles_rest_validation_error_positive(self):
        def on_get(self, context, **url):
            raise serializers.ValidationError({'err': ['msg']})

        self.assertEqual(self.patchE(on_get).status_code, 400)

    def test_override_endpoint_handler_positive(self):
        class OverriddenEndpoint(Endpoint):
            serializer = ConcreteSerializer
            config = { 'get': None }
            def on_get(self, context, **url):
                return {'test': 'ok'}, 201

        req = self.mock_request('GET')
        resp = OverriddenEndpoint.as_view()(req)
        self.assertEqual(resp.status_code, 201)
        self.assertDictEqual(resp.data, {'test': 'ok'})



class EndpointDefinitionLogicTests(TestCase):
    def test_empty_definition_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint(Endpoint):
                pass
        self.assertIn('`serializer` is required', ex.exception.args[0])

    def test_serializer_is_arbitrary_object_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint(Endpoint):
                serializer = 'foo'
        self.assertIn('`serializer` must be a class', ex.exception.args[0])

    def test_no_model_and_serializer_no_meta_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint(Endpoint):
                serializer = Serializer
        self.assertIn('Explicit `model` field is missing', ex.exception.args[0])

    def test_config_is_not_dict(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint(Endpoint):
                serializer = ConcreteSerializer
                config = 'foo'
        self.assertIn('`config` field must be of type `dict`', ex.exception.args[0])

    def test_unknown_method_foo_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint1(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'foo': {
                        'query': None
                    }
                }
        self.assertIn('unknown HTTP method `foo`', ex.exception.args[0])

    def test_query_is_not_callable_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint2(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'get': {
                        'query': None
                    }
                }
        self.assertIn('must be a callable', ex.exception.args[0])
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint7(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'get': {
                        'query': {'something_strange'},
                        'filters': {
                            'x': lambda x, y: (x, y)
                        }
                    }}
        self.assertIn('must be a callable', ex.exception.args[0])

    def test_get_filters_without_query_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint3(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'get': {
                        'filters': {
                            'y': lambda x, y: (x, y)
                        }
                    }}
        self.assertIn('cannot be used without', ex.exception.args[0])

    def test_get_filters_not_dict_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint5(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'get': {
                        'query': lambda x, y: (x, y),
                        'filters': lambda x, y: (x, y)
                    }}
        self.assertIn('field must be of type `dict`', ex.exception.args[0])

    def test_delete_called_without_query_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint8(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'delete': None
                }
        self.assertIn('`config` for `delete` must include', ex.exception.args[0])

    def test_url_fields_not_an_iterable_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint8(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'post': {
                        KW_CONFIG_URL_FIELDS: 'foo'
                    }
                }
        self.assertIn('field must be an iterable', ex.exception.args[0])

    def test_url_fields_is_iterable_posive(self):
        class MyEndpoint8(Endpoint):
            serializer = ConcreteSerializer
            config = {'post': {KW_CONFIG_URL_FIELDS: ('foo',)}}

        class MyEndpoint9(Endpoint):
            serializer = ConcreteSerializer
            config = {'post': {KW_CONFIG_URL_FIELDS: ['foo', ]}}

        class MyEndpoint10(Endpoint):
            serializer = ConcreteSerializer
            config = {'post': {KW_CONFIG_URL_FIELDS: {'foo', 'bar'}}}

    def test_get_with_filters_and_delete_with_query_positive(self):
        class MyEndpoint6(Endpoint):
            serializer = ConcreteSerializer
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

    def test_get_with_filters_positive(self):
        class MyEndpoint4(Endpoint):
            serializer = ConcreteSerializer
            config = {
                'get': {
                    'query': lambda x, y: (x, y),
                    'filters': {
                        'x': lambda x, y: (x, y)
                    }
                }}

    def test_transform_config_shorthands_positive(self):
        def are_equal(c1, c0):
            c1 = MetaEndpoint.transform_config_shorthands(c1)
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


class EndpointMiscTests(TestCase):
    def test_calling_as_view_with_empty_config_negative(self):
        with self.assertRaises(ImproperlyConfigured):
            class EmptyEndpoint(Endpoint):
                serializer = ConcreteSerializer

            EmptyEndpoint.as_view()

    def test_calling_endpoint_directly_raises_negative(self):
        with self.assertRaises(ImproperlyConfigured):
            ConcreteEndpoint()()

    def test_partial_application_correctness_returned_by_as_view_positive(self):
        ep = ConcreteEndpoint.as_view()
        self.assertFalse(inspect.isclass(ep.args[0]))
