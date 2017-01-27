#django-alt recipes

This document aims to provide a brief overview of functionality provided by
django-alt.

###0. Preparation
First let's create a simple model that will be managed as a REST resource:
```python
# models.py
class Todo(models.Model):
    text = models.TextField()
    slug = models.SlugField()
    date_created = models.DateTimeField(auto_now_add=True)
    
    @property
    def is_new(self):
        return (timezone.now() - self.date_created) < timedelta(hours=12)
```
Then let's create a `Validator`, that will:
 - constrain the values that the model can be constructed from,
 - prepare (clean) these values before construction,
 - allow access to the model's lifecycle,
```python
# validators.py
class TodoValidator(Validator):
    def clean(self, attrs):
        # generate a slug for the TODO
        attrs['slug'] = slugify(attrs['text'])
    
    def base(self, attrs):
        # we only allow TODOs that are more then 5 characters long
        invalid_if(len(attrs['text']) <= 5, 'text', 'The text is to short!')
    
    def did_create(self, instance, validated_attrs):
        # send emails to people that care about new TODOs
        inform_subscribers(instance)
        
```
And a simple serializer that will operate on all model fields:
```python
# serializers.py
class TodoSerializer(ValidatedModelSerializer):
    class Meta:
        model = Todo
        fields = '__all__'
        validator_class = TodoValidator
```


###1. Basic list and detail endpoints
```python
# endpoints.py
class TodoListEndpoint(Endpoint):
    """
    Provides TODO management entry points at collection level
    """
    serializer = TodoSerializer
    config = {
        'get': {
            # fetch all objects on GET
            'queryset': lambda todo, **url: todo.objects.all()
        },
        # no initial DB fetching needed for creating new TODOs 
        'post': None
    }
    
    
class TodoDetailEndpoint(Endpoint):
    """
    Provides TODO management entry points at instance level
    """
    serializer = TodoSerializer
    config = {
        'get, patch, delete': {
            # all HTTP methods operate on single objects enumerated by their ID
            'queryset': lambda todo, **url: todo.objects.get(id=url['pk'])
        }
    }
    
    
# urls.py
urlpatterns = [
    url(r'^/$', TodoListEndpoint.as_view()),
    url(r'^/(?P<pk>[0-9]+)/$', TodoDetailEndpoint.as_view()),
]
```