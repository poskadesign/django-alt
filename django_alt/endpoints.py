from django.core.exceptions import ImproperlyConfigured
from django.http import Http404

from django_alt.abstract.endpoints import MetaEndpoint
from django_alt.utils.shortcuts import queryset_has_many


class Endpoint(metaclass=MetaEndpoint):
    config = dict()
    model = None
    serializer = None
    view = None

    @classmethod
    def as_view(cls, **kwargs):
        """
        Main entry point for a request-response process.
        Allows to use handler.as_view() directly in urlpatterns.
        """
        if not len(cls.config):
            raise ImproperlyConfigured((
                'You are trying to call `as_view` on an endpoint with an empty config.\n'
                'Did you forget to specify the `config` attribute?\n'
                'Offending endpoint: `{0}`'
            ).format(cls.__name__))
        return cls.view.as_view(**kwargs)
		
		
	def __call__(self, *args, **kwargs):
        """
        Produces a more descriptive error message, when a call
        to `.as_view()` is missed in the URL configuration.
        :raises ImproperlyConfigured
        """
        raise ImproperlyConfigured((
            'You are trying to call an `Endpoint` object directly.\n'
            'Did you forget to use `.as_view()` in the URL configuration?\n'
            'Offending endpoint: `{0}`'
        ).format(self.__class__.__name__))

    """
    Default view handler implementations
    """

    @classmethod
    def on_get(cls, request, queryset, permission_test=None, **url) -> (dict, int):
        """
        Default GET handler implementation.
        Must return a tuple containing the response that is fed to the serializer and a status code.
        Safe to raise Validation, Permission and HTTP errors
        :param request: view request object
        :param queryset: queryset from the endpoint config
        :param permission_test: (optional) permission test to execute after full validation
        :param url: (optional) view url kwargs
        :return: {response_to_serialize, status_code}
        """
        if permission_test:
            cls.serializer._check_permissions(permission_test, request.data)
        return cls.serializer(queryset, many=queryset_has_many(queryset)).data, 200

    @classmethod
    def on_post(cls, request, permission_test=None, **url) -> (dict, int):
        """
        Default POST handler implementation.
        Used to create a new resource.
        Must return a tuple containing the response that is fed to the serializer and a status code.
        Safe to raise Validation, Permission and HTTP errors
        :param request: view request object
        :param permission_test: (optional) permission test to execute after full validation
        :param url: (optional) view url kwargs
        :return: {response_to_serialize, status_code}
        """
        is_many = isinstance(request.data, list)
        serializer = cls.serializer(data=request.data,
                                    permission_test=permission_test,
                                    many=is_many,
                                    request=request)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data, 201

    @classmethod
    def on_patch(cls, request, queryset, permission_test=None, **url) -> (dict, int):
        """
        Default PATCH handler implementation.
        Used to update an existing resource partially or fully.
        Must return a tuple containing the response that is fed to the serializer and a status code.
        Safe to raise Validation, Permission and HTTP errors
        :param request: view request object
        :param queryset: queryset from the endpoint config
        :param permission_test: permission test to execute after full validation
        :param url: view url kwargs
        :return: {response_to_serialize, status_code}
        """
        if queryset is None:
            raise Http404
        if queryset_has_many(queryset):
            raise NotImplementedError()
        serializer = cls.serializer(queryset,
                                    data=request.data,
                                    many=queryset_has_many(queryset),
                                    partial=True,
                                    permission_test=permission_test,
                                    request=request)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data, 200

    @classmethod
    def on_put(cls, request, queryset, permission_test=None, **url) -> (dict, int):
        """
        Default PUT handler implementation.
        Used to update an existing resource if it is defined and create a new one otherwise.
        Must return a tuple containing the response that is fed to the serializer and a status code.
        Safe to raise Validation, Permission and HTTP errors
        :param request: view request object
        :param queryset: queryset from the endpoint config
        :param permission_test: permission test to execute after full validation
        :param url: view url kwargs
        :return: {response_to_serialize, status_code}
        """
        if queryset is None:
            serializer = cls.serializer(data=request.data,
                                        many=queryset_has_many(queryset),
                                        permission_test=permission_test,
                                        request=request)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return serializer.data, 201

        if queryset_has_many(queryset):
            raise NotImplementedError()
        serializer = cls.serializer(queryset,
                                    data=request.data,
                                    partial=True,
                                    many=queryset_has_many(queryset),
                                    permission_test=permission_test,
                                    request=request)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data, 200

    @classmethod
    def on_delete(cls, request, queryset, permission_test=None, **url) -> (dict, int):
        """
        Default DELETE handler implementation.
        Used to delete an existing resource.
        Must return a tuple containing the response that is fed to the serializer and a status code.
        Safe to raise Validation, Permission and HTTP errors
        :param request: view request object
        :param queryset: queryset from the endpoint config
        :param permission_test: (optional) permission test to execute after full validation
        :param url: (optional) view url kwargs
        :return: {response_to_serialize, status_code}
        """
        if queryset is None:
            raise Http404
        validator = cls.serializer.Meta.validator_class(model=cls.model)
        validator.will_delete(queryset)
        cls.serializer._check_permissions(permission_test, request.data)
        data = cls.serializer(queryset, many=queryset_has_many(queryset)).data
        queryset.delete()
        validator.did_delete()
        return data, 200

    """
    Default permission handler implementations
    """

    @classmethod
    def can_default(cls):
        """
        Defines a pair of optional permission checker functions (pre_validation_func, post_validation_func).
        First is called initially before any validation.
        Second is called after validation finishes.
        They return a `bool` value and their calling signatures are as defined below.
        Alternatively these values can be used instead of callables:
            True  -> permission always granted,
            False -> permission never granted,
            None  -> no permission needed (True <=> None, the distinction is only semantic)
        :return: (pre_validation_func=None, post_validation_func=None)
        """
        return (
            lambda request, **url: True,
            lambda request, url, queryset, attrs: True
        )

    @classmethod
    def can_get(cls):
        return cls.can_default()

    @classmethod
    def can_post(cls):
        return cls.can_default()

    @classmethod
    def can_patch(cls):
        return cls.can_default()

    @classmethod
    def can_put(cls):
        return cls.can_default()

    @classmethod
    def can_delete(cls):
        return cls.can_default()
