class RequestContext:
    """
    Encapsulates data that is necessary to handle an `Endpoint` request
    """
    def __init__(self, request, *, queryset, permission_test):
        self.request = request
        self.queryset = queryset
        self.permission_test = permission_test
