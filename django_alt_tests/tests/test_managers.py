from unittest import mock
from unittest.mock import PropertyMock

from django.test import TestCase
from django_alt.managers import ValidatedManager

from django_alt.validators import Validator
from test_app.models import ModelA


class SampleValidator(Validator):
    def __init__(self, attrs, *, model=None, **context):
        self.calls = []
        super().__init__(attrs=attrs, model=model, **context)

    def default_field_1(self):
        return 'default'

    def clean_field_1(self, v):
        self.calls.append('clean_field_1')
        return v

    def clean_field_2(self, v):
        self.calls.append('clean_field_2')
        return v

    def field_field_1(self, v):
        self.calls.append('field_field_1')

    def field_field_2(self, v):
        self.calls.append('field_field_2')

    def check_x(self):
        self.calls.append('check_x')


class SampleManager(ValidatedManager):
    pass


class ValidatedManagerTestCase(TestCase):
    def assert_called(self, mock, what):
        return next(fun for fun in mock.mock_calls if what in str(fun))

    @mock.patch('tests.test_managers.SampleValidator')
    def test_create(self, mock):
        manager = SampleManager(ModelA, mock)
        attrs = dict(field_2=42, field_1='abc')
        type(mock.return_value).attrs = PropertyMock(return_value=attrs)

        instance = manager.do_create(**attrs)

        self.assert_called(mock, 'pre')
        self.assert_called(mock, 'clean')
        self.assert_called(mock, 'base')
        self.assert_called(mock, 'base_db')
        self.assert_called(mock, 'validate_fields')
        self.assert_called(mock, 'validate_checks')
        self.assert_called(mock, 'clean_and_default_fields')
        will_create_ = self.assert_called(mock, 'will_create')
        self.assert_called(mock, 'will_create_or_update')
        did_create_ = self.assert_called(mock, 'did_create')
        did_create_or_update = self.assert_called(mock, 'did_create_or_update')
        self.assert_called(mock, 'post')

        self.assertEqual(will_create_[1], ())
        self.assertEqual(did_create_[1], (instance,))
        self.assertEqual(did_create_or_update[1], (instance,))

        self.assertEqual(ModelA.objects.count(), 1)
        self.assertEqual(ModelA.objects.first().field_2, 42)
        self.assertEqual(ModelA.objects.first().field_1, 'abc')

    def test_create_deep_inspection(self):
        manager = SampleManager(ModelA, SampleValidator)
        attrs = dict(field_2=42, field_1='abc')
        manager.do_create(**attrs)
        assert len(set(manager.validator.calls).difference({'clean_field_1',
                                                            'clean_field_2',
                                                            'field_field_1',
                                                            'field_field_2',
                                                            'check_x'})) == 0

    @mock.patch('tests.test_managers.SampleValidator')
    def test_update(self, mock):
        instance = ModelA.objects.create(field_2=42, field_1='ltu')
        manager = SampleManager(ModelA, mock)
        attrs = dict(field_2=1337, field_1='ukr')
        type(mock.return_value).attrs = PropertyMock(return_value=attrs)

        instance = manager.do_update(instance, **attrs)

        self.assert_called(mock, 'pre')
        self.assert_called(mock, 'clean')
        self.assert_called(mock, 'base')
        self.assert_called(mock, 'base_db')
        self.assert_called(mock, 'validate_fields')
        self.assert_called(mock, 'validate_checks')
        self.assert_called(mock, 'clean_and_default_fields')
        will_update_ = self.assert_called(mock, 'will_update')
        self.assert_called(mock, 'will_create_or_update')
        did_update_ = self.assert_called(mock, 'did_update')
        did_create_or_update = self.assert_called(mock, 'did_create_or_update')
        self.assert_called(mock, 'post')

        self.assertEqual(will_update_[1], (instance,))
        self.assertEqual(did_update_[1], (instance,))
        self.assertEqual(did_create_or_update[1], (instance,))

        will_update_ = next(fun for fun in mock.mock_calls if 'will_update' in str(fun))
        did_update_ = next(fun for fun in mock.mock_calls if 'did_update' in str(fun))

        self.assertEqual(will_update_[1], (instance,))
        self.assertEqual(did_update_[1], (instance,))

        self.assertEqual(ModelA.objects.count(), 1)
        self.assertEqual(ModelA.objects.first().field_2, 1337)
        self.assertEqual(ModelA.objects.first().field_1, 'ukr')

    def test_update_deep_inspection(self):
        instance = ModelA.objects.create(field_2=42, field_1='ltu')
        manager = SampleManager(ModelA, SampleValidator)
        attrs = dict(field_2=1337, field_1='ukr')
        instance = manager.do_update(instance, **attrs)
        assert len(set(manager.validator.calls).difference({'clean_field_1',
                                                            'clean_field_2',
                                                            'field_field_1',
                                                            'field_field_2',
                                                            'check_x'})) == 0

    @mock.patch('tests.test_managers.SampleValidator')
    def test_delete(self, mock):
        instance = ModelA.objects.create(field_2=42, field_1='ltu')
        manager = SampleManager(ModelA, mock)
        self.assertEqual(ModelA.objects.count(), 1)

        attrs = dict(arbitrary='field')
        type(mock.return_value).attrs = PropertyMock(return_value=attrs)

        instance = manager.do_delete(instance, **attrs)

        self.assert_called(mock, 'pre')
        will_delete_ = next(fun for fun in mock.mock_calls if 'will_delete' in str(fun))
        did_delete_ = next(fun for fun in mock.mock_calls if 'did_delete' in str(fun))
        self.assert_called(mock, 'post')

        self.assertEqual(will_delete_[1], (instance,))
        self.assertEqual(did_delete_[1], (instance,))
        self.assertEqual(ModelA.objects.count(), 0)

    def test_calling_validate_only_without_a_validator_negative(self):
        manager = SampleManager(ModelA, SampleValidator)
        with self.assertRaises(AssertionError) as ex:
            manager.validate_only()

        self.assertIn('call `make_validator` on `SampleManager` before', ex.exception.args[0])

    def test_create_sets_is_create_flag_on_validator_positive(self):
        manager = SampleManager(ModelA, SampleValidator)
        manager.do_create(field_1='a', field_2=1)
        self.assertTrue(manager.validator.is_create)
        self.assertFalse(manager.validator.is_update)

    def test_create_sets_is_update_flag_on_validator_positive(self):
        manager = SampleManager(ModelA, SampleValidator)
        manager.do_create(field_1='a', field_2=1)
        self.assertTrue(manager.validator.is_create)
        self.assertFalse(manager.validator.is_update)
        manager.do_update(ModelA.objects.first(), field_1='a', field_2=1)
        self.assertTrue(manager.validator.is_update)
        self.assertFalse(manager.validator.is_create)

    def test_create_sets_default_field_positive(self):
        manager = SampleManager(ModelA, SampleValidator)
        obj = manager.do_create(field_2=1)
        self.assertEqual(obj.field_1, 'default')
