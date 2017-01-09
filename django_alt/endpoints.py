from django_alt.abstract.endpoints import MetaEndpoint
from django_alt.utils.shortcuts import queryset_has_many


class Endpoint(metaclass=MetaEndpoint):
    @classmethod
    def as_view(cls, **kwargs):
        """
        Main entry point for a request-response process.
        Allows to use handler.as_view() directly in urlpatterns.
        """
        return cls.view.as_view(**kwargs)

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
        :param [permission_test]: permission test to execute after full validation
        :param [url]: view url kwargs
        :return: (response_to_serialize, status_code)
        """
        if permission_test is not None and not permission_test(None):
            raise PermissionError()
        return cls.serializer(queryset, many=queryset_has_many(queryset)).data, 200

    """
    Default permission handler implementations
    """

    @classmethod
    def can_default(cls):
        """
        Defines a pair of optional permission checker functions (pre_validation_func, post_validation_func).
        First is called initially before any validation.
        Second is called after validation finishes.
        The methods return type `bool` and their calling signatures are as defined below.
        :return: (pre_validation_func=None, post_validation_func=None)
        """
        return (
            lambda request, **url: True,
            lambda request, queryset, attrs: True
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
