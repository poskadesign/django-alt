from functools import partial
from unittest import mock
from unittest.mock import PropertyMock, MagicMock

from django.test import TestCase

from django_alt_tests.conf.models import ModelA
from experimental.managers import ValidatedManager
from experimental.validators import Validator


class SampleValidator(Validator):
    def __init__(self, attrs, *, model=None, **context):
        self.calls = []
        super().__init__(attrs=attrs, model=model, **context)

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
    @mock.patch('tests.v1.test_managers.SampleValidator')
    def test_create(self, mock):
        manager = SampleManager(ModelA, SampleValidator)
        attrs = dict(field_2=42, field_1='abc')
        type(mock.return_value).attrs = PropertyMock(return_value=attrs)

        instance = manager.do_create(**attrs)

        assert_called = lambda what: next(fun for fun in mock.mock_calls if what in str(fun))

        assert_called('clean')
        assert_called('base')
        assert_called('base_db')
        assert_called('validate_fields')
        assert_called('validate_checks')
        assert_called('clean_fields')
        will_create_ = assert_called('will_create')
        did_create_ = assert_called('did_create')

        self.assertEqual(will_create_[1], ())
        self.assertEqual(did_create_[1], (instance,))

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

    @mock.patch('tests.v1.test_managers.SampleValidator')
    def test_update(self, mock):
        instance = ModelA.objects.create(field_2=42, field_1='ltu')
        manager = SampleManager(ModelA, SampleValidator)
        attrs = dict(field_2=1337, field_1='ukr')
        type(mock.return_value).attrs = PropertyMock(return_value=attrs)
        instance = manager.do_update(instance, **attrs)

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

    @mock.patch('tests.v1.test_managers.SampleValidator')
    def test_delete(self, mock):
        instance = ModelA.objects.create(field_2=42, field_1='ltu')
        manager = SampleManager(ModelA, SampleValidator)
        self.assertEqual(ModelA.objects.count(), 1)

        attrs = dict(arbitrary='field')
        type(mock.return_value).attrs = PropertyMock(return_value=attrs)

        instance = manager.do_delete(instance, **attrs)

        will_delete_ = next(fun for fun in mock.mock_calls if 'will_delete' in str(fun))
        did_delete_ = next(fun for fun in mock.mock_calls if 'did_delete' in str(fun))

        self.assertEqual(will_delete_[1], (instance,))
        self.assertEqual(did_delete_[1], (instance,))
        self.assertEqual(ModelA.objects.count(), 0)
