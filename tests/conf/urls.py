from django.conf.urls import url
from . import endpoints as e

urlpatterns = [
    url(r'^1$', e.ModelAEndpoint1.as_view(), name='e1'),
    url(r'^2$', e.ModelAEndpoint2.as_view(), name='e2'),
    url(r'^3$', e.ModelAEndpoint3.as_view(), name='e3'),
    url(r'^4$', e.ModelAEndpoint4.as_view(), name='e4'),
    url(r'^5$', e.ModelAEndpoint5.as_view(), name='e5'),
]
