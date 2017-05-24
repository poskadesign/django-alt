from functools import partial
from typing import Union, Type, Tuple

from django.core.exceptions import ValidationError as DjangoValidationError, ImproperlyConfigured
from django.http.response import HttpResponseBase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from django_alt.utils.shortcuts import invalid
from experimental.contexts import RequestContext
from experimental.dotdict import ddict

_HTTP_METHODS = ('get', 'post', 'patch', 'put', 'delete')

# todo prepend _
KW_CONFIG_FILTERS = 'filters'
KW_CONFIG_QUERYSET = 'query'
KW_CONFIG_URL_FIELDS = 'fields_from_url'
KW_CONFIG_URL_DONT_NORMALIZE = 'no_url_param_casting'


class _ViewProto:
    @staticmethod
    def apply_filters(qs, filters, query_params):
        current_param = None
        try:
            for param, func in filters.items():
                current_param = param
                if param in query_params:
                    qs = func(qs, query_params[param])
            return qs
        except DjangoValidationError as e:
            invalid(current_param, e.message)
        except ValueError as e:
            invalid(current_param, str(e))

    @staticmethod
    def defuse_response(responder, context):
        try:
            return responder(context)
        except:
            raise AssertionError()
            pass


    @staticmethod
    def respond(endpoint_self: Type['Endpoint'], request, *args, **kwargs):
        method = request.method.lower()
        config = endpoint_self.config.get(method, None)
        if config is None:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        # TODO solve for HEAD
        if KW_CONFIG_URL_DONT_NORMALIZE not in config:
            pass
            # TODO
            # url = _normalize_url(**kwargs)

        if KW_CONFIG_URL_FIELDS in config:
            # TODO
            try:
                pass
            except KeyError as ex:
                pass

        queryset = None
        if KW_CONFIG_QUERYSET in config:
            queryset = config[KW_CONFIG_QUERYSET](endpoint_self.model, **kwargs)
            if KW_CONFIG_FILTERS in config and len(request.query_params):
                queryset = _ViewProto.apply_filters(queryset, config[KW_CONFIG_FILTERS], request.query_params)

        context = RequestContext(request, queryset=queryset, permission_test=None)
        response = _ViewProto.defuse_response(getattr(endpoint_self, 'on_' + method), context)

        try:
            if isinstance(response, dict):
                # response: dict
                return Response(*response)
            elif isinstance(response, HttpResponseBase):
                # response: Response
                return response
            elif isinstance(response, tuple) and len(response) == 2:
                # response: Tuple[dict, int]
                assert isinstance(response[0], dict) and isinstance(response[1], int)
                return Response(*response)
            raise TypeError()
        except (TypeError, AssertionError, KeyError):
            raise AssertionError(
                (
                    'Incorrect return type on method `on_{}`.\n'
                    'Endpoint methods starting with `on_` must return either:\n'
                    ' - response_data: dict\n'
                    ' - response_obj: rest_framework.response.Response\n'
                    ' - (response_data, status_code): (dict, int)\n'
                    'Offending endpoint: `{}`.'
                ).format(method, endpoint_self.__class__.__name__))


class MetaEndpoint(type):
    def __new__(mcs, name, bases, namespace):
        if len(bases):
            # only transform for classes extending `Endpoint`
            namespace = mcs.transform_namespace(name, namespace)
        return type.__new__(mcs, name, bases, namespace)

    @classmethod
    def transform_namespace(mcs, clsname, namespace):
        assert 'serializer' in namespace, (
            'Field `serializer` is required for an endpoint definition.\n'
            'Offending Endpoint `{}`'
        ).format(clsname)

        try:
            if not issubclass(namespace['serializer'], BaseSerializer):
                raise AssertionError()
        except:
            raise AssertionError('Field `serializer` must be a class extending `BaseSerializer`.\n'
                                 'Offending Endpoint `{}`'.format(clsname))

        if 'model' not in namespace:
            assert hasattr(namespace['serializer'], 'Meta') and hasattr(namespace['serializer'].Meta, 'model'), (
                'Explicit `model` field is missing and trying to get\n'
                'the `model` from the `Meta` declared on the given serializer failed\n'
                'at endpoint `{}`.'
            ).format(clsname)
            namespace['model'] = namespace['serializer'].Meta.model

        namespace['config'] = mcs.transform_config(clsname, namespace.get('config', {}))

        return namespace

    @classmethod
    def transform_config_shorthands(mcs, config):
        result = {}
        for k, v in config.items():
            if v is None:
                v = {}
            if ',' in k:
                for end in k.split(','):
                    result.setdefault(end.strip(), {}).update(v)
            else:
                result.setdefault(k.strip(), {}).update(v)
        return result

    @classmethod
    def transform_config(mcs, clsname, config):
        assert isinstance(config, dict), (
            'Endpoint `config` field must be of type `dict`. Offending endpoint `{}`'
        ).format(clsname)

        if len(config):
            config = mcs.transform_config_shorthands(config)
            for method_name, method_config in config.items():
                assert method_name in _HTTP_METHODS, (
                    'Endpoint `{}` config definition contains an unknown HTTP method `{}`.\n'
                    'Allowed methods are `{}`.'
                ).format(clsname, method_name, _HTTP_METHODS)

                if KW_CONFIG_QUERYSET in method_config:
                    assert callable(method_config['query']), (
                        '`{}` field in endpoint `config` must be a callable accepting '
                        'parameters: `model` and `**url` in endpoint `{}`'
                    ).format(KW_CONFIG_QUERYSET, clsname)

                    if KW_CONFIG_FILTERS in method_config:
                        assert isinstance(method_config[KW_CONFIG_FILTERS], dict), (
                            '`{}` field must be of type `dict`, containing pairs of `filter_name`, '
                            '`filter_func(queryset, value)` in endpoint `{}`'
                        ).format(KW_CONFIG_FILTERS, clsname)

                elif method_name == 'delete':
                    raise AssertionError(('`config` for `delete` must include '
                                          '`{}` field for endpoint `{}`').format(KW_CONFIG_QUERYSET, clsname))

                elif KW_CONFIG_FILTERS in method_config:
                    raise AssertionError('`{}` cannot be used without `{}` in endpoint `{}`'
                                         .format(KW_CONFIG_FILTERS, KW_CONFIG_QUERYSET, clsname))

                if KW_CONFIG_URL_FIELDS in method_config:
                    assert hasattr(method_config[KW_CONFIG_URL_FIELDS], '__iter__') \
                           and not isinstance(method_config[KW_CONFIG_URL_FIELDS], str), (
                        '`{}` config field must be an iterable in endpoint `{}`'
                    ).format(KW_CONFIG_URL_FIELDS, clsname)

                if KW_CONFIG_URL_DONT_NORMALIZE in method_config:
                    if KW_CONFIG_URL_DONT_NORMALIZE is not True:
                        del method_config[KW_CONFIG_URL_DONT_NORMALIZE]
        return config


class Endpoint(metaclass=MetaEndpoint):
    """
    Base class with default view and permission implementations
    """
    config = ddict()
    model, serializer = None, None

    def __call__(self, *args, **kwargs):
        """
        Produces a more descriptive error message, when a call
        to `.as_view()` is missed in the URL configuration.
        :raises ImproperlyConfigured
        """
        raise ImproperlyConfigured(('You are trying to call an `Endpoint` object directly.\n'
                                    'Did you forget to use `.as_view()` in the URL configuration?\n'
                                    'Offending endpoint: `{0}`'
                                    ).format(self.__class__.__qualname__))

    @classmethod
    def as_view(cls):
        """
        Acts as a main entry point for a request-response process,
        allowing to use `MyEndpoint.as_view()` directly in urlpatterns.
        :raises ImproperlyConfigured
        """
        if not len(cls.config):
            raise ImproperlyConfigured(('You are trying to call `as_view` on an endpoint with an empty config.\n'
                                        'Did you forget to specify the `config` attribute?\n'
                                        'Offending endpoint: `{0}`'
                                        ).format(cls.__qualname__))
        return partial(_ViewProto.respond, cls())

    """
    Default view handler implementations
    """

    def on_get(self, context: Type[RequestContext], **url) -> Union[Response, dict, Tuple[dict, int]]:
        pass
