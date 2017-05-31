import json
from functools import partial

from django.core.exceptions import ValidationError as DjangoValidationError, ObjectDoesNotExist
from django.http import Http404
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django_alt.utils.shortcuts import invalid, try_cast, first_defined

base_view_class = APIView
http_methods = ('get', 'post', 'patch', 'put', 'delete')

KW_CONFIG_FILTERS = 'filters'
KW_CONFIG_QUERYSET = 'query'
KW_CONFIG_URL_FIELDS = 'fields_from_url'
KW_CONFIG_URL_DONT_NORMALIZE = 'no_url_param_casting'


def _apply_filters(qs, filters, query_params):
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


def _normalize_url(**url):
    def cast(value):
        return first_defined(
            try_cast(int, value),
            try_cast(float, value),
            value
        )
    return {k: cast(v) for k, v in url.items()}


def _view_prototype(view_self, request, **url):
    method = request.method.lower()
    if method == 'head':
        method = 'get'
    endpoint = view_self.endpoint_class

    try:
        config = endpoint.config[method]

        if KW_CONFIG_URL_DONT_NORMALIZE not in config:
            url = _normalize_url(**url)

        if KW_CONFIG_URL_FIELDS in config:
            try:
                # TODO find another way
                # explicitly loads data to _full_data
                request.data
                updated_fragment = {k: url[k] for k in config[KW_CONFIG_URL_FIELDS]}
                if isinstance(request._full_data, list):
                    for member in request._full_data:
                        assert isinstance(member, dict), (
                            'An endpoint that accepts a nested list of items\n'
                            'cannot have `fields_from_url` config set.\n'
                            'Offending endpoint: `{}`, method: `{}`.\n'
                            '`request.data` dump: \n`{}`'
                        ).format(endpoint.__name__, request.method, request._full_data)
                        member.update(updated_fragment)
                else:
                    request._full_data = request._full_data.copy()
                    request._full_data.update(updated_fragment)
            except KeyError:
                raise AssertionError(('Key supplied in `{0}` was not present in the url dict at endpoint `{1}`.\n'
                                      '`{0}` dump: {2}').format(KW_CONFIG_URL_FIELDS, view_self.endpoint_class.__name__,
                                                                json.dumps(config[KW_CONFIG_URL_FIELDS])))

        qs = None
        pre_can, post_can = getattr(endpoint, 'can_' + method)()

        # pre_can/post_can meaning
        if pre_can is not None and pre_can is not True:
            if pre_can is False or not pre_can(request, **url):
                raise PermissionError()

        if KW_CONFIG_QUERYSET in config:
            qs = config[KW_CONFIG_QUERYSET](endpoint.model, **url)
            if KW_CONFIG_FILTERS in config and len(request.query_params):
                qs = _apply_filters(qs, config[KW_CONFIG_FILTERS], request.query_params)

        if post_can is not None and post_can is not True:
            post_can = partial(post_can, request, url, qs)
        handler = getattr(endpoint, 'on_' + method)
        if method == 'post':
            return Response(*handler(request, post_can, **url))
        return Response(*handler(request, qs, post_can, **url))

    except serializers.ValidationError as e:
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

    except PermissionError:
        return Response(status=status.HTTP_401_UNAUTHORIZED if request.user.is_anonymous else status.HTTP_403_FORBIDDEN)

    except Http404:
        return Response(status=status.HTTP_404_NOT_FOUND)

    except ObjectDoesNotExist as e:
        return Response(' '.join(e.args), status=status.HTTP_404_NOT_FOUND)

    except DjangoValidationError as e:
        return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)


class MetaEndpoint(type):
    def __new__(mcs, name, bases, clsdict):
        if len(bases):
            mcs.transform_fields(name, clsdict)
            if len(clsdict['config']):
                clsdict['view'] = mcs.make_view_class(name + 'View', clsdict['config'])
        cls = super().__new__(mcs, name, bases, clsdict)
        if len(bases) and len(clsdict['config']):
            cls.view.endpoint_class = cls
        return cls
        
    def __call__(cls, *args, **kwargs):
        """
        Produces a more descriptive error message, when a call
        to `.as_view()` is missed in the URL configuration.
        :raises ImproperlyConfigured
        """
        raise ImproperlyConfigured((
            'You are trying to call an `Endpoint` object directly.\n'
            'Did you forget to use `.as_view()` in the URL configuration?\n'
        ))

    @staticmethod
    def transform_config_shorthands(config_dict: dict) -> dict:
        result = {}
        for k, v in config_dict.items():
            if v is None:
                v = {}
            if ',' in k:
                for end in k.split(','):
                    result.setdefault(end.strip(), {}).update(v)
            else:
                result.setdefault(k.strip(), {}).update(v)
        return result

    @staticmethod
    def transform_fields(name, clsdict):
        assert 'serializer' in clsdict, (
            'Field `serializer` is required for an endpoint definition. '
            'Offending Endpoint `{0}`'
        ).format(name)

        if 'model' not in clsdict:
            assert hasattr(clsdict['serializer'].Meta, 'model'), (
                'Explicit model field is missing and trying to get '
                'the model from the serializer failed at endpoint `{0}`.'
            ).format(name)
            clsdict['model'] = clsdict['serializer'].Meta.model

        config = clsdict.get('config', {})
        if len(config):
            assert isinstance(config, dict), (
                'Endpoint `config` field must be of type `dict`. Offending endpoint `{0}`'
            ).format(name)
            config = MetaEndpoint.transform_config_shorthands(config)

            for method_name, contents in config.items():
                assert method_name in http_methods, (
                    'Endpoint `{0}` config definition contains an unknown HTTP method `{2}`. '
                    'Allowed methods are `{1}`.'
                ).format(name, http_methods, method_name)

                if isinstance(contents, dict):
                    if KW_CONFIG_QUERYSET in contents:
                        assert callable(contents['query']), (
                            '`{0}` field in Endpoint `config` must be a callable accepting '
                            'parameters: `model` and `**url` in endpoint `{1}`'
                        ).format(KW_CONFIG_QUERYSET, name)
                        if 'filters' in contents:
                            assert isinstance(contents[KW_CONFIG_FILTERS], dict), (
                                '`{0}` field must be of type `dict`, containing pairs of `filter_name`, '
                                '`filter_func(queryset, value)` in endpoint `{1}`'
                            ).format(KW_CONFIG_FILTERS, name)

                    elif method_name == 'delete':
                        raise AssertionError(('`config` for `delete` must include '
                                              '`{0}` field for endpoint `{1}`').format(KW_CONFIG_QUERYSET, name))

                    elif KW_CONFIG_FILTERS in contents:
                        raise AssertionError('`{0}` cannot be used without `{1}` in endpoint `{2}`'
                                             .format(KW_CONFIG_FILTERS, KW_CONFIG_QUERYSET, name))

                    if KW_CONFIG_URL_FIELDS in contents:
                        assert hasattr(contents[KW_CONFIG_URL_FIELDS], '__iter__'), (
                            '`{0}` config field must be an iterable in endpoint `{1}`'
                        ).format(KW_CONFIG_URL_FIELDS, name)

                    if KW_CONFIG_URL_DONT_NORMALIZE in contents:
                        if KW_CONFIG_URL_DONT_NORMALIZE is not True:
                            del contents[KW_CONFIG_URL_DONT_NORMALIZE]

        clsdict['config'] = config

    @staticmethod
    def make_view_class(name, config: dict):
        body = {method: _view_prototype for method, _ in config.items()}
        return type(name, (base_view_class,), body)
