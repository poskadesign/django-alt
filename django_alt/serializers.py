from collections import OrderedDict

from rest_framework import serializers
from rest_framework.fields import empty

from .abstract.serializers import BaseValidatedSerializer


class ValidatedSerializer(BaseValidatedSerializer, serializers.Serializer):
    def __init__(self, instance=None, data=empty, *, validator_class=None, **kwargs):
        if not hasattr(self, 'Meta'):
            self.Meta = type('Meta', tuple(), dict())
        if validator_class:
            setattr(self.Meta, 'validator_class', validator_class)

        assert hasattr(self.Meta, 'validator_class'), (
            'Either a `validator_class` set on the serializer Meta or '
            'provided when initializing the serializer is required.'
            'Offending serializer: {0}'
        ).format(self.__class__.__qualname__)

        self.Meta.validator_instance = self.Meta.validator_class()

        super().__init__(instance, data, **kwargs)

    def to_representation(self, instance) -> OrderedDict:
        representation = super().to_representation(instance)
        return self.Meta.validator_instance.to_representation(representation, self.validated_data)


class ValidatedModelSerializer(ValidatedSerializer, serializers.ModelSerializer):
    pass