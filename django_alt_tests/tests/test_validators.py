from django.test import TestCase
from django_alt.dotdict import ddict

from django_alt.validators import Validator


class ValidatorsMiscTests(TestCase):
    def test_attrs_setter_converts_to_ddict_positive(self):
        validator = Validator(dict(a=1))
        self.assertTrue(isinstance(validator.attrs, ddict))

        validator.attrs = dict(a=2)
        self.assertTrue(isinstance(validator.attrs, ddict))

    def test_is_create_accessed_when_it_was_not_passed_as_context_negative(self):
        validator = Validator(dict(a=1))
        with self.assertRaises(AssertionError) as ex:
            validator.is_create
        self.assertIn('`is_create` or `is_update` accessor was invoked. Offending validator: `Validator`',
                      ex.exception.args[0])

    def test_is_create_accessed_positive(self):
        validator = Validator(dict(a=1), is_create=True)
        self.assertTrue(validator.is_create)

    def test_is_update_accessed_when_it_was_not_passed_as_context_negative(self):
        validator = Validator(dict(a=1))
        with self.assertRaises(AssertionError) as ex:
            validator.is_update
        self.assertIn('`is_create` or `is_update` accessor was invoked. Offending validator: `Validator`',
                      ex.exception.args[0])

    def test_is_update_accessed_positive(self):
        validator = Validator(dict(a=1), is_create=True)
        self.assertFalse(validator.is_update)

