from rest_framework import serializers

from experimental.managers import ValidatedManager


class ValidatedSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        print('VS')
        super().__init__(*args, **kwargs)


class ValidatedModelSerializer(ValidatedSerializer, serializers.ModelSerializer, ValidatedManager):
    def __init__(self, *args, **kwargs):
        print('VMS')
        assert hasattr(self.Meta, 'model'), (
            'Missing `model` field in serializer Meta class. '
            'Offending serializer: {}').format(self.__class__.__qualname__)
        assert hasattr(self.Meta, 'validator'), (
            'Missing `validator` field in serializer Meta class. '
            'Offending serializer: {}').format(self.__class__.__qualname__)

        super().__init__(*args, model_class=self.Meta.model, validator_class=self.Meta.validator, **kwargs)

    def validate(self, attrs):
        return self.validate_only(**attrs)

    def create(self, validated_data):
        return self.do_create()

    def update(self, instance, validated_data):
        return self.do_update(instance)

