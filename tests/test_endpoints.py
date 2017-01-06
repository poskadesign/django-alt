from unittest.mock import patch

from django.test import TestCase

from django_alt.endpoints import Endpoint


class MetaEndpointTests(TestCase):
    pass


class EndpointTests(TestCase):
    def test_required_fields(self):
        with self.assertRaises(AssertionError):
            class MyEndpoint(Endpoint):
                pass
    pass
