from collections import OrderedDict

from rest_framework import serializers

from .abstract.serializers import BaseValidatedSerializer


class ValidatedModelSerializer(BaseValidatedSerializer, serializers.ModelSerializer):
    def _instantiate_validator(self, **kwargs):
        assert hasattr(self.Meta, 'model'), (
            'Missing `model` field in serializer Meta class. '
            'Offending serializer: {0}'
        ).format(self.__class__.__name__)
        return self.Meta.validator_class(model=self.Meta.model, **kwargs)

    def create(self, validated_data: dict):
        instance = super().create(validated_data)
        self.validator.did_create(instance, validated_data)
        return instance

    def update(self, instance, validated_data: dict):
        instance = super().update(instance, validated_data)
        self.validator.did_update(instance, validated_data)
        return instance

    def to_representation(self, instance) -> OrderedDict:
        representation = super().to_representation(instance)
        return self.validator_instance.to_representation(representation, self.validated_data)
