from rest_framework.views import APIView

base_view_class = APIView


class MetaEndpoint(type):
    def __new__(mcs, name, bases, clsdict):
        mcs.transform_fields(clsdict)
        return super().__new__(mcs, name, bases, clsdict)

    def transform_fields(cls, clsdict):
        assert 'serializer' in clsdict, (
            'Field `serializer` is required for an endpoint definition. '
            'Offending Endpoint'

        )
        pass

    def make_view_class(cls, name, config: dict):
        pass
