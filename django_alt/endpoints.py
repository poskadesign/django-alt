from django_alt.abstract.endpoints import MetaEndpoint


class Endpoint(metaclass=MetaEndpoint):
    @classmethod
    def as_view(cls, **kwargs):
        """
        Main entry point for a request-response process.
        Allows to use handler.as_view() directly in urlpatterns.
        """
        return cls.view.as_view(**kwargs)
