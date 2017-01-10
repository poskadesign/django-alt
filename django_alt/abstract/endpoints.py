from functools import partial

from django.core.exceptions import ValidationError as DjangoValidationError, ObjectDoesNotExist
from django.http import Http404
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django_alt.utils.shortcuts import invalid

base_view_class = APIView
http_methods = ('get', 'post', 'patch', 'put', 'delete')


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


def _view_prototype(view_self, request, **url):
    method = request.method.lower()
    if method == 'head':
        method = 'get'
    endpoint = view_self.endpoint_class

    try:
        config = endpoint.config[method]
        qs = None
        pre_can, post_can = getattr(endpoint, 'can_' + method)()
        if pre_can is not None and not pre_can(request, **url):
            raise PermissionError()

        if 'query' in config:
            qs = config['query'](endpoint.model, **url)
            if 'filters' in config and len(request.query_params):
                qs = _apply_filters(qs, config['filters'], request.query_params)

        if post_can is not None:
            post_can = partial(post_can, request, qs)
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

    except (ObjectDoesNotExist, DjangoValidationError) as e:
        return Response(' '.join(e.args), status=status.HTTP_400_BAD_REQUEST)


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

    @staticmethod
    def transform_config(config_dict: dict) -> dict:
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
            config = MetaEndpoint.transform_config(config)

            for method_name, contents in config.items():
                assert method_name in http_methods, (
                    'Endpoint `{0}` config definition contains an unknown HTTP method `{2}`. '
                    'Allowed methods are `{1}`.'
                ).format(name, http_methods, method_name)

                if isinstance(contents, dict):
                    if 'query' in contents:
                        assert callable(contents['query']), (
                            '`query` field in Endpoint `config` must be a callable accepting '
                            'parameters: `model` and `**url` in endpoint `{0}`'
                        ).format(name)
                        if 'filters' in contents:
                            assert isinstance(contents['filters'], dict), (
                                '`filters` field must be of type `dict`, containing pairs of `filter_name`, '
                                '`filter_func(queryset, value)` in endpoint `{0}`'
                            ).format(name)

                    elif method_name == 'delete':
                        raise AssertionError(('`config` for `delete` must include '
                                              '`query` field for endpoint `{0}`').format(name))

                    elif 'filters' in contents:
                        raise AssertionError('`filters` cannot be used without `query` in endpoint `{0}`'.format(name))

        clsdict['config'] = config

    @staticmethod
    def make_view_class(name, config: dict):
        body = {method: _view_prototype for method, _ in config.items()}
        return type(name, (base_view_class,), body)
