from unittest.mock import patch

from django.test import TestCase
from rest_framework import serializers

from django_alt.abstract.serializers import BaseValidatedSerializer
from django_alt.abstract.validators import Validator
from django_alt.serializers import ValidatedModelSerializer
from django_alt.utils.shortcuts import invalid, invalid_if, if_in
from django_alt_tests.conf.models import ModelA


def generate_serializer(validator_class):
    cls = validator_class

    class ConcreteSerializer(BaseValidatedSerializer):
        somestring = serializers.CharField()

        class Meta:
            validator_class = cls

        def create(self, validated_data):
            self.Meta.validator_instance.did_create(validated_data, validated_data)
            return validated_data

    return ConcreteSerializer


def serialize(validator, data):
    serializer = generate_serializer(validator)(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save()


class BaseValidatedSerializerTests(TestCase):
    def setUp(self):
        self.validator_class = type('ConcreteValidator', (Validator,), dict())

    def test_init_with_no_validator_class(self):
        class ConcreteSerializer(BaseValidatedSerializer): pass

        with self.assertRaises(AssertionError):
            inst = ConcreteSerializer()

    def test_init_with_validator_class(self):
        class ConcreteSerializer(BaseValidatedSerializer):
            pass

        inst = ConcreteSerializer(validator_class=self.validator_class)
        self.assertTrue(hasattr(inst, 'Meta'))
        self.assertTrue(hasattr(inst.Meta, 'validator_class'))
        self.assertEqual(inst.Meta.validator_class, self.validator_class)

    def test_init_with_validator_class_in_meta(self):
        class ConcreteSerializer(BaseValidatedSerializer):
            class Meta:
                validator_class = self.validator_class

        inst = generate_serializer(self.validator_class)()
        self.assertEqual(inst.Meta.validator_class, self.validator_class)

    def test_create_no_validation(self):
        class ConcreteValidator(Validator):
            pass

        data = {'somestring': 'a cool string'}
        self.assertEqual(serialize(ConcreteValidator, data)['somestring'], 'a cool string')

    def test_create_with_validation_clean(self):
        class ConcreteValidator(Validator):
            def clean(self, attrs: dict):
                attrs['somestring'] = attrs['somestring'].upper()

        data = {'somestring': 'a cool string'}
        self.assertEqual(serialize(ConcreteValidator, data)['somestring'], 'A COOL STRING')

    def test_create_with_validation_base(self):
        class ConcreteValidator(Validator):
            def base(self, attrs: dict):
                invalid_if(len(attrs['somestring']) > 5, 'somestring', 'too long')

            def will_create(self, attrs: dict):
                raise ArithmeticError('should stop at base')

            def base_db(self, attrs: dict):
                raise ArithmeticError('should stop at base')

        data = {'somestring': 'a cool string'}
        with self.assertRaises(serializers.ValidationError):
            serialize(ConcreteValidator, data)

    def test_create_with_validation_will_create(self):
        class ConcreteValidator(Validator):
            def will_create(self, attrs: dict):
                invalid_if(len(attrs['somestring']) > 5, 'somestring', 'too long')

        data = {'somestring': 'a cool string'}
        with self.assertRaises(serializers.ValidationError):
            serialize(ConcreteValidator, data)

    def test_create_with_validation_base_db(self):
        class ConcreteValidator(Validator):
            def base_db(self, attrs: dict):
                invalid('somestring', 'already in db')

        data = {'somestring': 'a cool string'}
        with self.assertRaises(serializers.ValidationError):
            serialize(ConcreteValidator, data)

    def test_create_with_validation_did_create(self):
        class ConcreteValidator(Validator):
            def clean(self, attrs: dict):
                if_in('somestring', attrs, lambda a: a.upper())

            def did_create(self, instance, validated_attrs: dict):
                assert 'somestring' in instance
                assert instance['somestring'] == 'A COOL STRING'
                assert validated_attrs['somestring'] == 'A COOL STRING'
                raise serializers.ValidationError('reached')

        data = {'somestring': 'a cool string'}
        with self.assertRaises(serializers.ValidationError) as ex:
            serialize(ConcreteValidator, data)
        self.assertEqual(ex.exception.detail[0], 'reached')

    def test_create_with_validation_to_representation(self):
        class ConcreteValidator(Validator):
            def to_representation(self, repr_attrs, validated_attrs=None):
                repr_attrs['something'] = 1
                return repr_attrs

        data = {'somestring': 'a cool string'}
        serializer = generate_serializer(ConcreteValidator)(data=data)
        serializer.is_valid(raise_exception=True)
        self.assertTrue('something' in serializer.data)
        self.assertEqual(serializer.data['something'], 1)


class ValidatedModelSerializerTests(TestCase):
    def setUp(self):
        class ModelAValidator(Validator):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                assert hasattr(self, 'model')
                assert self.model == ModelA

            def clean(self, attrs: dict):
                attrs['field_1'] = 'a' + attrs['field_1']

            def clean_field_1(self, field_1):
                return 'works' if field_1.startswith('z') else field_1

            def base(self, attrs: dict):
                attrs['field_1'] = 'a' + attrs['field_1']

            def field_field_1(self, value):
                invalid_if('c' in value, 'field_1', 'Boom')

            def check_something(self, attrs):
                invalid_if('d' in attrs['field_1'], 'field_1', 'Boom')

            def will_create(self, attrs: dict):
                invalid_if(self.model.objects.count(), '', '')

        class ModelASerializer(ValidatedModelSerializer):
            class Meta:
                validator_class = ModelAValidator
                model = ModelA
                fields = '__all__'

        self.ModelAValidator = ModelAValidator
        self.ModelASerializer = ModelASerializer

    def test_create(self):
        with patch.object(self.ModelAValidator, 'will_create', return_value=None) as m1:
            with patch.object(self.ModelAValidator, 'did_create', return_value=None) as m2:
                serializer = self.ModelASerializer(data={'field_1': 'somestr', 'field_2': 15})
                serializer.is_valid(raise_exception=True)
                serializer.save()

        self.assertTrue(m1.called and m2.called)

        self.assertEqual(ModelA.objects.count(), 1)
        self.assertEqual(ModelA.objects.first().field_1, 'aasomestr')
        self.assertEqual(ModelA.objects.first().field_2, 15)

    def test_update(self):
        instance = ModelA.objects.create(field_1='otherstr', field_2=25)

        with patch.object(self.ModelAValidator, 'will_update', return_value=None) as m1:
            with patch.object(self.ModelAValidator, 'did_update', return_value=None) as m2:
                serializer = self.ModelASerializer(instance, data={'field_1': 'somestr', 'field_2': 15})
                serializer.is_valid(raise_exception=True)
                serializer.save()

        self.assertTrue(m1.called and m2.called)

        self.assertEqual(ModelA.objects.count(), 1)
        self.assertEqual(ModelA.objects.first().id, instance.id)
        self.assertEqual(ModelA.objects.first().field_1, 'aasomestr')
        self.assertEqual(ModelA.objects.first().field_2, 15)

    def test_validate_fields_negative(self):
        instance = ModelA.objects.create(field_1='otherstr', field_2=25)
        serializer = self.ModelASerializer(instance, data={'field_1': 'somecstr', 'field_2': 15})
        with self.assertRaises(serializers.ValidationError) as ex:
            serializer.is_valid(raise_exception=True)
        self.assertEqual(ex.exception.detail['field_1'][0], 'Boom.')

    def test_check_negative(self):
        instance = ModelA.objects.create(field_1='otherstr', field_2=25)
        serializer = self.ModelASerializer(instance, data={'field_1': 'somedstr', 'field_2': 15})
        with self.assertRaises(serializers.ValidationError) as ex:
            serializer.is_valid(raise_exception=True)
        self.assertEqual(ex.exception.detail['field_1'][0], 'Boom.')

    def test_clean_fields_negative(self):
        instance = ModelA.objects.create(field_1='otherstr', field_2=25)
        serializer = self.ModelASerializer(instance, data={'field_1': 'zzz', 'field_2': 15})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(ModelA.objects.first().field_1, 'aaworks')