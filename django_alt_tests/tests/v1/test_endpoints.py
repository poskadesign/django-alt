import inspect

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import TestCase
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.utils.serializer_helpers import ReturnList

from django_alt_tests.conf.models import ModelA
from experimental.endpoints import Endpoint, KW_CONFIG_URL_FIELDS, MetaEndpoint
from experimental.serializers import ValidatedSerializer, ValidatedModelSerializer
from experimental.validators import Validator


class ConcreteSerializer(ValidatedSerializer):
    class Meta:
        model = ModelA


class ConcreteValidator(Validator):
    pass


class ConcreteModelSerializer(ValidatedModelSerializer):
    class Meta:
        model = ModelA
        validator = ConcreteValidator
        fields = '__all__'


class ConcreteEndpoint(Endpoint):
    serializer = ConcreteSerializer
    config = {
        'get': None
    }


class EndpointBaseViewLogicTests(TestCase):
    def setUp(self):
        class EBase(Endpoint):
            serializer = ConcreteSerializer
            config = {'get': None}

        self.EBase = EBase
        ModelA.objects.create(field_1='a', field_2=1)
        ModelA.objects.create(field_1='b', field_2=2)

    def patchE(self, method, is_anonymous=False):
        self.EBase.on_get = method
        return self.EBase.as_view()(self.mock_request('GET', is_anonymous))

    def mock_request(self, method, is_anonymous=False, data=None):
        return type('RequestMock', tuple(), dict(
            method=method,
            user=type('UserMock', tuple(), dict(is_anonymous=is_anonymous)),
            data=data
        ))

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

        def on_get_9(self, context, **url):
            return [1, 2, 3]

        def on_get_10(self, context, **url):
            return ReturnList([1, 2, 3], serializer=None)

        for method in (on_get_1, on_get_3, on_get_7, on_get_8):
            with self.assertRaises(AssertionError):
                self.patchE(method)

        all((self.patchE(on_get_4), self.patchE(on_get_5),
             self.patchE(on_get_6), self.patchE(on_get_9), self.patchE(on_get_10)))

    def test_overridden_endpoint_handler_handles_rest_validation_error_positive(self):
        def on_get(self, context, **url):
            raise serializers.ValidationError({'err': ['msg']})

        self.assertEqual(self.patchE(on_get).status_code, 400)

    def test_overridden_endpoint_handler_handles_django_validation_error_positive(self):
        def on_get(self, context, **url):
            raise ValidationError({'err': ['msg']})

        self.assertEqual(self.patchE(on_get).status_code, 400)

    def test_overridden_endpoint_handler_handles_permission_error_not_logged_in_positive(self):
        def on_get(self, context, **url):
            raise PermissionError()

        self.assertEqual(self.patchE(on_get, True).status_code, 401)

    def test_overridden_endpoint_handler_handles_permission_error_logged_in_positive(self):
        def on_get(self, context, **url):
            raise PermissionError()

        self.assertEqual(self.patchE(on_get, False).status_code, 403)

    def test_overridden_endpoint_handler_handles_django_http404_positive(self):
        def on_get(self, context, **url):
            get_object_or_404(ModelA, field_1__exact='nonexistent field')

        self.assertEqual(self.patchE(on_get).status_code, 404)
        self.assertEqual(self.patchE(on_get).data, {'non_field_errors': ['No ModelA matches the given query.']})

    def test_overridden_endpoint_handler_handles_object_does_not_exist_positive(self):
        def on_get(self, context, **url):
            ModelA.objects.get(field_1__exact='nonexistent field')

        self.assertEqual(self.patchE(on_get).status_code, 404)
        self.assertEqual(self.patchE(on_get).data, {'non_field_errors': ['ModelA matching query does not exist.']})

    """
    GET handlers
    """

    def test_default_get_none_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {'get': None}

        response = ConcreteEndpoint.as_view()(self.mock_request('GET'))
        self.assertDictEqual(response.data, {'field_2': None, 'field_1': ''})
        self.assertEqual(response.status_code, 200)

    def test_default_get_single_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'get': {
                    'query': lambda model, **url: model.objects.first()
                }
            }

        response = ConcreteEndpoint.as_view()(self.mock_request('GET'))
        self.assertDictEqual(response.data, {'id': 1, 'field_2': 1, 'field_1': 'a'})
        self.assertEqual(response.status_code, 200)

    def test_default_get_many_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'get': {
                    'query': lambda model, **url: model.objects.all()
                }
            }

        response = ConcreteEndpoint.as_view()(self.mock_request('GET'))
        self.assertListEqual(response.data,
                             [{'id': 1, 'field_2': 1, 'field_1': 'a'}, {'id': 2, 'field_2': 2, 'field_1': 'b'}])
        self.assertEqual(response.status_code, 200)

    def test_override_get_endpoint_handler_positive(self):
        class OverriddenEndpoint(Endpoint):
            serializer = ConcreteSerializer
            config = {'get': None}

            def on_get(self, context, **url):
                return {'test': 'ok'}, 201

        resp = OverriddenEndpoint.as_view()(self.mock_request('GET'))
        self.assertEqual(resp.status_code, 201)
        self.assertDictEqual(resp.data, {'test': 'ok'})

    """
    POST handlers
    """

    def test_default_post_none_and_data_none_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'post': None
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('POST'))
        self.assertEqual(resp.status_code, 400)
        self.assertDictEqual(resp.data, {'non_field_errors': ['No data provided']})

    def test_default_post_none_and_data_empty_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'post': None
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('POST', data={}))
        self.assertEqual(resp.status_code, 400)
        self.assertDictEqual(resp.data,
                             {'field_2': ['This field is required.'], 'field_1': ['This field is required.']})

    def test_default_post_single_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'post': None
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('POST', data={'field_2': 1, 'field_1': 'a'}))
        self.assertEqual(resp.status_code, 201)
        self.assertDictEqual(resp.data, {'id': 3, 'field_2': 1, 'field_1': 'a'})
        self.assertEqual(ModelA.objects.count(), 3)
        self.assertEqual(ModelA.objects.last().id, 3)
        self.assertEqual(ModelA.objects.last().field_2, 1)
        self.assertEqual(ModelA.objects.last().field_1, 'a')

    def test_default_post_many_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'post': None
            }

        resp = ConcreteEndpoint.as_view()(
            self.mock_request('POST', data=[{'field_2': 1, 'field_1': 'a'}, {'field_2': 2, 'field_1': 'b'}]))
        self.assertEqual(resp.status_code, 201)
        self.assertListEqual(resp.data,
                             [{'id': 3, 'field_2': 1, 'field_1': 'a'}, {'id': 4, 'field_2': 2, 'field_1': 'b'}])
        self.assertEqual(ModelA.objects.count(), 4)
        self.assertEqual(ModelA.objects.all()[2].id, 3)
        self.assertEqual(ModelA.objects.all()[2].field_2, 1)
        self.assertEqual(ModelA.objects.all()[2].field_1, 'a')
        self.assertEqual(ModelA.objects.all()[3].id, 4)
        self.assertEqual(ModelA.objects.all()[3].field_2, 2)
        self.assertEqual(ModelA.objects.all()[3].field_1, 'b')

    def test_default_post_many_not_allowed_handler_negative(self):
        with self.assertRaises(AssertionError):
            class ConcreteEndpoint(Endpoint):
                serializer = ConcreteModelSerializer
                config = {
                    'post': None,
                    'allow_many': False
                }

            ConcreteEndpoint.as_view()(
                self.mock_request('POST', data=[{'field_2': 1, 'field_1': 'a'}, {'field_2': 2, 'field_1': 'b'}]))

    """
    PATCH handlers
    """

    def test_default_patch_query_returns_none_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'patch': {
                    'query': lambda *args, **kwargs: None
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('PATCH'))
        self.assertEqual(resp.status_code, 404)

    def test_default_patch_query_raises_no_data_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'patch': {
                    'query': lambda model, **url: ModelA.objects.get(field_1='nonexistent')
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('PATCH'))
        self.assertEqual(resp.status_code, 404)
        self.assertDictEqual(resp.data, {'non_field_errors': ['ModelA matching query does not exist.']})

    def test_default_patch_query_raises_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'patch': {
                    'query': lambda model, **url: ModelA.objects.get(field_1='nonexistent')
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('PATCH', data={'field_2': 5}))
        self.assertEqual(resp.status_code, 404)
        self.assertDictEqual(resp.data, {'non_field_errors': ['ModelA matching query does not exist.']})

    def test_default_patch_none_and_data_none_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'patch': {
                    'query': lambda model, **url: ModelA.objects.first()
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('PATCH'))
        self.assertEqual(resp.status_code, 400)
        self.assertDictEqual(resp.data, {'non_field_errors': ['No data provided']})

    def test_default_patch_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'patch': {
                    'query': lambda model, **url: ModelA.objects.first()
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('PATCH', data={'field_1': 'updated'}))
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.data, {'id': 1, 'field_2': 1, 'field_1': 'updated'})
        self.assertEqual(ModelA.objects.first().field_1, 'updated')
        self.assertEqual(ModelA.objects.first().field_2, 1)
        self.assertEqual(ModelA.objects.first().id, 1)

    """
        DELETE handlers
    """

    def test_default_delete_query_returns_none_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'delete': {
                    'query': lambda *args, **kwargs: None
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('DELETE'))
        self.assertEqual(resp.status_code, 404)

    def test_default_delete_query_raises_no_data_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'delete': {
                    'query': lambda model, **url: ModelA.objects.get(field_1='nonexistent')
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('DELETE'))
        self.assertEqual(resp.status_code, 404)
        self.assertDictEqual(resp.data, {'non_field_errors': ['ModelA matching query does not exist.']})

    def test_default_delete_query_raises_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'delete': {
                    'query': lambda model, **url: ModelA.objects.get(field_1='nonexistent')
                }
            }

        resp = ConcreteEndpoint.as_view()(self.mock_request('DELETE', data={'field_2': 5}))
        self.assertEqual(resp.status_code, 404)
        self.assertDictEqual(resp.data, {'non_field_errors': ['ModelA matching query does not exist.']})

    def test_default_delete_none_and_data_none_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'delete': {
                    'query': lambda model, **url: ModelA.objects.first()
                }
            }

        count = ModelA.objects.all().count()
        resp = ConcreteEndpoint.as_view()(self.mock_request('DELETE'))
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.data, {'id': None, 'field_2': 1, 'field_1': 'a'})
        self.assertEqual(ModelA.objects.all().count(), count - 1)
        self.assertEqual(ModelA.objects.first().id, 2)

    def test_default_delete_handler_positive(self):
        class ConcreteEndpoint(Endpoint):
            serializer = ConcreteModelSerializer
            config = {
                'delete': {
                    'query': lambda model, **url: ModelA.objects.first()
                }
            }

        count = ModelA.objects.all().count()
        resp = ConcreteEndpoint.as_view()(self.mock_request('DELETE', data={'field_1': 'updated'}))
        self.assertEqual(resp.status_code, 200)
        self.assertDictEqual(resp.data, {'id': None, 'field_2': 1, 'field_1': 'a'})
        self.assertEqual(ModelA.objects.all().count(), count - 1)
        self.assertEqual(ModelA.objects.first().id, 2)


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

    def test_method_definition_is_not_passed_an_iterable_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint2(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'get': lambda a: a
                }
        self.assertIn('Incorrectly formed endpoint config object', ex.exception.args[0])

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

    def test_patch_includes_query_attribute_negative(self):
        with self.assertRaises(AssertionError) as ex:
            class MyEndpoint8(Endpoint):
                serializer = ConcreteSerializer
                config = {
                    'patch': {}
                }
        self.assertIn('`patch` method config must include', ex.exception.args[0])

    def test_url_fields_is_iterable_positive(self):
        class MyEndpoint8(Endpoint):
            serializer = ConcreteSerializer
            config = {'post': {KW_CONFIG_URL_FIELDS: ('foo',)}}

        class MyEndpoint9(Endpoint):
            serializer = ConcreteSerializer
            config = {'post': {KW_CONFIG_URL_FIELDS: ['foo', ]}}

        class MyEndpoint10(Endpoint):
            serializer = ConcreteSerializer
            config = {'post': {KW_CONFIG_URL_FIELDS: {'foo', 'bar'}}}

    def test_allow_many_flag_set_to_true_automatically_positive(self):
        class MyEndpoint6(Endpoint):
            serializer = ConcreteSerializer
            config = {
                'get': {'query': lambda x, y: (x, y), },
                'post': {'query': lambda x, y: (x, y), },
                'put': {'query': lambda x, y: (x, y), },
                'patch': {'query': lambda x, y: (x, y), },
                'delete': {'query': lambda x, y: (x, y), },
            }

        self.assertTrue(MyEndpoint6.config['get'].allow_many)
        self.assertTrue(MyEndpoint6.config.post.allow_many)
        self.assertTrue(MyEndpoint6.config.put.allow_many)
        self.assertTrue(MyEndpoint6.config.patch.allow_many)
        self.assertTrue(MyEndpoint6.config.delete.allow_many)

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
            c1 = MetaEndpoint.transform_config_shorthands('MockEndpoint', c1)
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
