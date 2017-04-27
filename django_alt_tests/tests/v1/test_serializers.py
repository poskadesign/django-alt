from django.test import TestCase

from django_alt_tests.conf.models import ModelA
from experimental.serializers import ValidatedModelSerializer
from experimental.validators import Validator


class ConcreteValidator(Validator):
    pass


class ConcreteSerializer(ValidatedModelSerializer):
    class Meta:
        model = ModelA
        validator = ConcreteValidator


class ValidatedModelSerializerTests(TestCase):
    def test_basic_creation_positive(self):
        serializer = ConcreteSerializer(data=dict(field_1='abc', field_2=1337))
        serializer.is_valid(raise_exception=True)
        serializer.save()