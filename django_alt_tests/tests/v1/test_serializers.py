from django.db.models import QuerySet, Model
from django.test import TestCase
from typing import Type

from django_alt_tests.conf.models import ModelA
from experimental.serializers import ValidatedModelSerializer
from experimental.validators import Validator


class ConcreteValidator(Validator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callstack = []

    def did_create(self, instance: Type[Model]):
        self.callstack.append('did_create')

    def clean(self):
        self.callstack.append('clean')

    def will_update(self, instance: Type[Model]):
        self.callstack.append('will_update')

    def will_create(self):
        self.callstack.append('will_create')

    def base_db(self):
        self.callstack.append('base_db')

    def did_update(self, instance: Type[Model]):
        self.callstack.append('did_update')

    def will_read(self, instance: Type[Model]):
        self.callstack.append('will_read')

    def base(self):
        self.callstack.append('base')

    def will_delete(self, queryset: Type[QuerySet]):
        self.callstack.append('will_delete')

    def did_delete(self, queryset: Type[QuerySet]):
        self.callstack.append('did_delete')


class ConcreteSerializer(ValidatedModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = []

    def do_create(self, **attrs):
        self.calls.append('do_create')
        return super().do_create(**attrs)

    def do_update(self, instance, **attrs):
        self.calls.append('do_update')
        return super().do_update(instance, **attrs)

    class Meta:
        model = ModelA
        validator = ConcreteValidator
        fields = '__all__'


class ValidatedModelSerializerTests(TestCase):
    def test_basic_creation_positive(self):
        serializer = ConcreteSerializer(data=dict(field_1='abc', field_2=1337))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        self.assertEqual(ModelA.objects.count(), 1)
        self.assertEqual(ModelA.objects.first(), obj)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.field_1, 'abc')
        self.assertEqual(obj.field_2, 1337)

        self.assertEqual(len(serializer.calls), 1)
        self.assertEqual(serializer.calls[0], 'do_create')

        self.assertEqual(serializer.validator.callstack, ['clean', 'base', 'will_create', 'base_db', 'did_create'])

    def test_basic_reading_positive(self):
        obj = ModelA.objects.create(field_1='abc', field_2=1337)
        serializer = ConcreteSerializer(obj)
        data = serializer.data
        self.assertDictEqual(data, {
            'id': 1,
            'field_1': 'abc',
            'field_2': 1337,
        })
        self.assertEqual(serializer.validator.callstack, ['will_read'])

    def test_basic_creation_and_reading_positive(self):
        serializer = ConcreteSerializer(data=dict(field_1='abc', field_2=1337))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data

        self.assertEqual(len(serializer.calls), 1)
        self.assertEqual(serializer.calls[0], 'do_create')

        self.assertEqual(serializer.validator.callstack,
                         ['clean', 'base', 'will_create', 'base_db', 'did_create', 'will_read'])
        self.assertDictEqual(data, {
            'id': 1,
            'field_1': 'abc',
            'field_2': 1337,
        })

    def test_basic_update_positive(self):
        obj = ModelA.objects.create(field_1='abc', field_2=1337)
        serializer = ConcreteSerializer(obj, data=dict(field_1='def', field_2=43))
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()

        self.assertEqual(len(serializer.calls), 1)
        self.assertEqual(serializer.calls[0], 'do_update')
        self.assertEqual(serializer.validator.callstack, ['clean', 'base', 'will_update', 'base_db', 'did_update'])
        self.assertEqual(ModelA.objects.count(), 1)
        self.assertEqual(ModelA.objects.first(), obj)
        self.assertEqual(obj.id, 1)
        self.assertEqual(obj.field_1, 'def')
        self.assertEqual(obj.field_2, 43)

    def test_basic_update_and_reading_positive(self):
        obj = ModelA.objects.create(field_1='abc', field_2=1337)
        serializer = ConcreteSerializer(obj, data=dict(field_1='def', field_2=43))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data

        self.assertEqual(len(serializer.calls), 1)
        self.assertEqual(serializer.calls[0], 'do_update')
        self.assertEqual(serializer.validator.callstack,
                         ['clean', 'base', 'will_update', 'base_db', 'did_update', 'will_read'])
        self.assertDictEqual(data, {
            'id': 1,
            'field_1': 'def',
            'field_2': 43,
        })
