from rest_framework import serializers

from .abstract.serializers import BaseValidatedSerializer


class ValidatedModelSerializer(BaseValidatedSerializer, serializers.ModelSerializer):
    def _instantiate_validator(self, **kwargs):
        assert hasattr(self.Meta, 'model'), (
            'Missing `model` field in serializer Meta class. '
            'Offending serializer: {0}').format(self.__class__.__name__)
        return self.Meta.validator_class(model=self.Meta.model, serializer=self, **kwargs)

    def create(self, validated_data: dict):
        instance = super().create(validated_data)
        self.validator.did_create(instance, validated_data)
        return instance

    def update(self, instance, validated_data: dict):
        instance = super().update(instance, validated_data)
        self.validator.did_update(instance, validated_data)
        return instance


class ValidatedModelListSerializer(serializers.ListSerializer):
    def create(self, validated_data: dict):
        raise NotImplementedError()

    def update(self, instance, validated_data: dict):
        raise NotImplementedError()
