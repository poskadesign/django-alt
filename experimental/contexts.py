from django_alt.utils.shortcuts import queryset_has_many


class RequestContext:
    """
    Encapsulates data that is necessary to handle an `Endpoint` request
    """

    def __init__(self, request, *, queryset):
        self.request = request
        self.queryset = queryset

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
        return self.request.data
