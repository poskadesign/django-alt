from functools import partial
from typing import Union, Type, Tuple

from django.core.exceptions import ValidationError as django_ValidationError, ImproperlyConfigured, ObjectDoesNotExist
from django.http.response import HttpResponseBase, Http404
from rest_framework import status
from rest_framework.fields import empty
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ValidationError as drf_ValidationError

from django_alt.utils.shortcuts import invalid, make_error
from experimental.contexts import RequestContext
from experimental.dotdict import ddict, undefined
from experimental.exceptions import EndpointError
from experimental.serializers import ValidatedSerializer

_HTTP_METHODS = ('get', 'post', 'patch', 'put', 'delete')

# todo prepend _
_KW_CONFIG_FILTERS = 'filters'
_KW_CONFIG_QUERYSET = 'query'
_KW_CONFIG_URL_FIELDS = 'fields_from_url'
_KW_CONFIG_URL_DONT_NORMALIZE = 'no_url_param_casting'
_KW_CONFIG_ALLOW_MANY = 'allow_many'
_KW_ALL = {_KW_CONFIG_FILTERS, _KW_CONFIG_QUERYSET,
           _KW_CONFIG_URL_FIELDS, _KW_CONFIG_URL_DONT_NORMALIZE,
           _KW_CONFIG_ALLOW_MANY}


class ViewPrototype:
    @staticmethod
    def apply_filters(qs, filters, query_params):
        current_param = None
        try:
            for param, func in filters.items():
                current_param = param
                if param in query_params:
                    qs = func(qs, query_params[param])
            return qs
        except django_ValidationError as e:
            invalid(current_param, e.message)
        except ValueError as e:
            invalid(current_param, str(e))

    @staticmethod
    def defuse_response(responder, get_context):
        context = None
        try:
            context = get_context()
            return responder(context)
        except EndpointError as e:
            return e.status_code
        except drf_ValidationError as e:
            return e.detail, status.HTTP_400_BAD_REQUEST
        except django_ValidationError as e:
            return e.message_dict, status.HTTP_400_BAD_REQUEST
        except PermissionError:
            if context is not None and context.request.user.is_anonymous:
                return status.HTTP_401_UNAUTHORIZED
            return status.HTTP_403_FORBIDDEN
        except (Http404, ObjectDoesNotExist) as e:
            return make_error(None, ', '.join(e.args)), status.HTTP_404_NOT_FOUND

    @staticmethod
    def respond(endpoint_self: Type['Endpoint'], request, *args, **kwargs):
        method = request.method.lower()
        config = endpoint_self.config.get(method, None)
        if config is None:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

        # TODO solve for HTTP HEAD
        if _KW_CONFIG_URL_DONT_NORMALIZE not in config:
            pass
            # TODO
            # url = _normalize_url(**kwargs)

        if _KW_CONFIG_URL_FIELDS in config:
            # TODO
            try:
                pass
            except KeyError as ex:
                pass

        def get_context():
            # TODO check for multiple filters!
            queryset = None
            try:
                if _KW_CONFIG_QUERYSET in config:
                    queryset = config[_KW_CONFIG_QUERYSET](endpoint_self.model, **kwargs)
                    if _KW_CONFIG_FILTERS in config and len(request.query_params):
                        queryset = ViewPrototype.apply_filters(queryset, config[_KW_CONFIG_FILTERS], request.query_params)
            except ObjectDoesNotExist:
                if method != 'put':
                    raise
                queryset = None
            return RequestContext(request, queryset=queryset, url_args=args, url_kwargs=kwargs)

        responder = getattr(endpoint_self, 'on_' + method)
        result = ViewPrototype.defuse_response(responder, get_context)

        try:
            if isinstance(result, int):
                # result: int
                return Response(None, result)
            elif isinstance(result, HttpResponseBase):
                # result: Response
                return result

            status_code = None
            if isinstance(result, tuple) and len(result) == 2:
                # result: Tuple[dict, int]
                assert isinstance(result[1], int)
                status_code, result = result[1], result[0]

            if isinstance(result, dict) or isinstance(result, list):
                # result: dict
                return Response(result, status=status_code)
            raise TypeError()
        except (TypeError, AssertionError, KeyError):
            raise AssertionError(
                (
                    'Incorrect return type on method `on_{}`.\n'
                    'Endpoint methods starting with `on_` must return either:\n'
                    ' - response_data: dict\n'
                    ' - response_obj: Response\n'
                    ' - response_data, status_code: (dict, int)\n'
                    ' - status_code: int (response_data is empty)\n'
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
    def transform_config_shorthands(mcs, clsname, config):
        result = ddict()
        for k, v in config.items():
            if v is None:
                v = ddict()
            if ',' in k:
                for end in k.split(','):
                    result.setdefault(end.strip(), ddict()).update(v)
            else:
                assert hasattr(v, '__iter__'), (
                    'Incorrectly formed endpoint config object:\n'
                    '\tvalue at key `{}` must be an iterable, not `{}`.\n'
                    'Offending endpoint: `{}`, definition.'
                ).format(k.strip(), v.__class__.__name__, clsname)
                result.setdefault(k.strip(), ddict()).update(v)
        return result

    @classmethod
    def transform_config(mcs, clsname, config):
        assert isinstance(config, dict), (
            'Endpoint `config` field must be of type `dict`. Offending endpoint `{}`'
        ).format(clsname)

        if len(config):
            config = mcs.transform_config_shorthands(clsname, config)
            for method_name, method_config in config.items():
                assert method_name in _HTTP_METHODS, (
                    'Endpoint `{}` config definition contains an unknown HTTP method `{}`.\n'
                    'Allowed methods are `{}`.'
                ).format(clsname, method_name, _HTTP_METHODS)

                assert len(set(method_config.keys()).difference(_KW_ALL)) == 0, (
                    '`{}` {} config contains unknown keys: `{}`.'
                ).format(clsname, method_name, ', '.join(sorted(set(method_config.keys()).difference(_KW_ALL))))

                if method_name == 'patch':
                    assert _KW_CONFIG_QUERYSET in method_config, (
                        'Endpoint `patch` method config must include the `{}` attribute.\n'
                        'Offending endpoint: `{}`'
                    ).format(_KW_CONFIG_QUERYSET, clsname)

                method_config.setdefault(_KW_CONFIG_ALLOW_MANY, True)

                if _KW_CONFIG_QUERYSET in method_config:
                    assert callable(method_config[_KW_CONFIG_QUERYSET]), (
                        '`{}` field in endpoint `config` must be a callable accepting '
                        'parameters: `model` and `**url` in endpoint `{}`'
                    ).format(_KW_CONFIG_QUERYSET, clsname)

                    if _KW_CONFIG_FILTERS in method_config:
                        assert isinstance(method_config[_KW_CONFIG_FILTERS], dict), (
                            '`{}` field must be of type `dict`, containing pairs of `filter_name`, '
                            '`filter_func(queryset, value)` in endpoint `{}`'
                        ).format(_KW_CONFIG_FILTERS, clsname)

                elif method_name == 'delete':
                    raise AssertionError(('`config` for `delete` must include '
                                          '`{}` field for endpoint `{}`').format(_KW_CONFIG_QUERYSET, clsname))

                elif _KW_CONFIG_FILTERS in method_config:
                    raise AssertionError('`{}` cannot be used without `{}` in endpoint `{}`'
                                         .format(_KW_CONFIG_FILTERS, _KW_CONFIG_QUERYSET, clsname))

                if _KW_CONFIG_URL_FIELDS in method_config:
                    assert hasattr(method_config[_KW_CONFIG_URL_FIELDS], '__iter__') \
                           and not isinstance(method_config[_KW_CONFIG_URL_FIELDS], str), (
                        '`{}` config field must be an iterable in endpoint `{}`'
                    ).format(_KW_CONFIG_URL_FIELDS, clsname)

                if _KW_CONFIG_URL_DONT_NORMALIZE in method_config:
                    if _KW_CONFIG_URL_DONT_NORMALIZE is not True:
                        del method_config[_KW_CONFIG_URL_DONT_NORMALIZE]
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
        return partial(ViewPrototype.respond, cls())

    @classmethod
    def make_serializer(cls, context: RequestContext, data=empty, many=None, **kwargs) -> ValidatedSerializer:
        """
        a DRY shortcut for quickly instantiating an assigned serializer.
        :param context: a `RequestContext` object to extract the queryset from
        :param data: request data that shall be serialized
        :param many: a bool flag, that when set, means more than one object will be serialized
        :return: serializer instance
        """
        extra_kwargs = dict(context=context) if issubclass(cls.serializer, ValidatedSerializer) else {}
        extra_kwargs.update(kwargs)
        if context.queryset is None:
            return cls.serializer(data=data,
                                  many=context.data_has_many if many is None else many,
                                  **extra_kwargs)
        return cls.serializer(instance=context.queryset,
                              data=data,
                              many=context.queryset_has_many if many is None else many,
                              **extra_kwargs)

    def _create_and_serialize(self, context, allow_many=undefined):
        serializer = self.make_serializer(context, context.data, context.data_has_many if allow_many else False)
        return ValidatedSerializer.validate_and_save(serializer)

    """
    Default view handler implementations
    """

    def on_get(self, context: RequestContext) -> Union[Response, int, dict, Tuple[dict, int]]:
        return self.make_serializer(context).data

    def on_post(self, context: RequestContext) -> Union[Response, int, dict, Tuple[dict, int]]:
        return self._create_and_serialize(context, self.config.post.allow_many), 201

    def on_put(self, context: RequestContext) -> Union[Response, int, dict, Tuple[dict, int]]:
        if context.queryset is None:
            return self._create_and_serialize(context, self.config.put.allow_many), 201

        serializer = self.make_serializer(context, context.data)
        return ValidatedSerializer.validate_and_save(serializer), 200

    def on_patch(self, context: RequestContext) -> Union[Response, int, dict, Tuple[dict, int]]:
        if context.queryset is None:
            raise EndpointError(status.HTTP_404_NOT_FOUND)

        serializer = self.make_serializer(context, context.data, partial=True)
        return ValidatedSerializer.validate_and_save(serializer), 200

    def on_delete(self, context: RequestContext) -> Union[Response, int, dict, Tuple[dict, int]]:
        if context.queryset is None:
            raise EndpointError(status.HTTP_404_NOT_FOUND)

        serializer = self.make_serializer(context)
        serializer.delete()
        return serializer.data
