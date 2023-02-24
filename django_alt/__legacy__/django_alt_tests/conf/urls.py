from django.conf.urls import url
from . import endpoints as e

urlpatterns = [
    url(r'^1$', e.ModelAEndpoint1.as_view(), name='e1'),
    url(r'^2$', e.ModelAEndpoint2.as_view(), name='e2'),
    url(r'^3$', e.ModelAEndpoint3.as_view(), name='e3'),
    url(r'^4$', e.ModelAEndpoint4.as_view(), name='e4'),
    url(r'^5$', e.ModelAEndpoint5.as_view(), name='e5'),
    url(r'^6$', e.ModelAEndpoint6.as_view(), name='e6'),
    url(r'^7$', e.ModelAEndpoint7.as_view(), name='e7'),
    url(r'^8$', e.ModelAEndpoint8.as_view(), name='e8'),
    url(r'^9/(?P<field_1>\w+)/(?P<field_2>[0-9]+)/$', e.ModelAEndpoint9.as_view(), name='e9'),
    url(r'^10/(?P<field_1>\w+)/(?P<field_2>[0-9]+)/$', e.ModelAEndpoint10.as_view(), name='e10'),
]
