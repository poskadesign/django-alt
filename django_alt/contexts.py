from django_alt.utils.shortcuts import queryset_has_many
from django_alt.dotdict import ddict


class RequestContext:
    """
    Encapsulates data that is necessary to handle an `Endpoint` request
    """

    def __init__(self, request, *, data, queryset, query_params=None, url_args=None, url_kwargs=None):
        self.request = request
        self.queryset = queryset
        self.url_args = url_args
        self.url_kwargs = url_kwargs
        self.query_params = query_params
        self._data = ddict(data)

    @property
    def queryset_has_many(self):
        return queryset_has_many(self.queryset)

    @property
    def data_has_many(self):
        return isinstance(self.data, list)

    @property
    def data(self):
        """
        Shorthand returning data property of the associated request
        """
        return self._data

    @property
    def user(self):
        return self.request.user