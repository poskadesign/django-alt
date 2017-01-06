# from rest_framework.views import APIView

# base_view_class = APIView


class MetaEndpoint(type):
    def __new__(mcs, name, bases, clsdict):
        if len(bases):
            mcs.transform_fields(mcs, name, clsdict)
        return super().__new__(mcs, name, bases, clsdict)

    def transform_fields(mcs, name, clsdict):
        assert 'serializer' in clsdict, (
            'Field `serializer` is required for an endpoint definition. '
            'Offending Endpoint `{0}`'
        ).format(name)

    def make_view_class(cls, name, config: dict):
        pass
