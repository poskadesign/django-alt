from django.test import TestCase

from experimental.dotdict import ddict
from experimental.validators import Validator


class ValidatorsMiscTests(TestCase):
    def test_attrs_setter_converts_to_ddict_positive(self):
        validator = Validator(dict(a=1))
        self.assertTrue(isinstance(validator.attrs, ddict))

        validator.attrs = dict(a=2)
        self.assertTrue(isinstance(validator.attrs, ddict))
