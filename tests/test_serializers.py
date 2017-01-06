from unittest import TestCase

from rest_framework import serializers

from django_alt.abstract.validators import BaseValidator
from django_alt.serializers import ValidatedSerializer, ValidatedModelSerializer
from django_alt.utils.shortcuts import invalid, invalid_if, if_in


def generate_serializer(validator_class):
    cls = validator_class

    class ConcreteSerializer(ValidatedSerializer):
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


class ValidatedSerializerTests(TestCase):
    def setUp(self):
        self.validator_class = type('ConcreteValidator', (BaseValidator,), dict())

    def test_init_with_no_validator_class(self):
        class ConcreteSerializer(ValidatedSerializer): pass

        with self.assertRaises(AssertionError):
            inst = ConcreteSerializer()

    def test_init_with_validator_class(self):
        class ConcreteSerializer(ValidatedSerializer):
            pass

        inst = ConcreteSerializer(validator_class=self.validator_class)
        self.assertTrue(hasattr(inst, 'Meta'))
        self.assertTrue(hasattr(inst.Meta, 'validator_class'))
        self.assertEqual(inst.Meta.validator_class, self.validator_class)

    def test_init_with_validator_class_in_meta(self):
        class ConcreteSerializer(ValidatedSerializer):
            class Meta:
                validator_class = self.validator_class

        inst = generate_serializer(self.validator_class)()
        self.assertEqual(inst.Meta.validator_class, self.validator_class)

    def test_create_no_validation(self):
        class ConcreteValidator(BaseValidator):
            pass

        data = {'somestring': 'a cool string'}
        self.assertEqual(serialize(ConcreteValidator, data)['somestring'], 'a cool string')

    def test_create_with_validation_clean(self):
        class ConcreteValidator(BaseValidator):
            def clean(self, attrs: dict):
                attrs['somestring'] = attrs['somestring'].upper()

        data = {'somestring': 'a cool string'}
        self.assertEqual(serialize(ConcreteValidator, data)['somestring'], 'A COOL STRING')

    def test_create_with_validation_base(self):
        class ConcreteValidator(BaseValidator):
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
        class ConcreteValidator(BaseValidator):
            def will_create(self, attrs: dict):
                invalid_if(len(attrs['somestring']) > 5, 'somestring', 'too long')

        data = {'somestring': 'a cool string'}
        with self.assertRaises(serializers.ValidationError):
            serialize(ConcreteValidator, data)

    def test_create_with_validation_base_db(self):
        class ConcreteValidator(BaseValidator):
            def base_db(self, attrs: dict):
                invalid('somestring', 'already in db')

        data = {'somestring': 'a cool string'}
        with self.assertRaises(serializers.ValidationError):
            serialize(ConcreteValidator, data)

    def test_create_with_validation_did_create(self):
        class ConcreteValidator(BaseValidator):
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
        class ConcreteValidator(BaseValidator):
            def to_representation(self, repr_attrs, validated_attrs=None):
                repr_attrs['something'] = 1
                return repr_attrs

        data = {'somestring': 'a cool string'}
        serializer = generate_serializer(ConcreteValidator)(data=data)
        serializer.is_valid(raise_exception=True)
        self.assertTrue('something' in serializer.data)
        self.assertEqual(serializer.data['something'], 1)


class ValidatedModelSerializerTests(TestCase):
    def test_init(self):
        ValidatedModelSerializer
