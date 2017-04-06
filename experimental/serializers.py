from rest_framework import serializers

from experimental.managers import ValidatedManager


class ValidatedSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ValidatedModelSerializer(ValidatedSerializer, ValidatedManager, serializers.ModelSerializer):
    def validate(self, attrs):
        return self.validate_only(**attrs)

    def create(self, validated_data):
        return self.do_create()

    def update(self, instance, validated_data):
        return self.do_update(instance)


class SomeSerializer(ValidatedSerializer):
    def do_create(self, **attrs):
        # override behaviour
        pass
