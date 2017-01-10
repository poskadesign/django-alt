#django-alt

django-alt is an alternative approach to data validation and 
REST endpoint definition in Django and DRF.

###Motives
- No standardized way to separate *domain* and *data* logic.
- No standardized way to validate serialized data.
- Standard validation techniques do not offer any mechanisms for *separation of concerns* 
(e.g. validating object creation vs. update)
- Cumbersome lifecycle hooks (e.g. code to execute upon object creation)

This package aims to solve these problems.

###Example: Todo list
#####endpoints.py
```python
class TodoEndpoint(Endpoint):
    serializer = TodoSerializer
    config = {
        'get, patch, delete': {
            'queryset': lambda todo, **url: todo.objects.get(id=url['pk'])
        }
    }
```
#####validators.py
```python
class TodoValidator(Validator):
    def clean(self, attrs):
        attrs['slug'] = slugify(attrs['name'])
        
    def will_create(self, attrs):
        invalid_if(not attrs['author'].is_active, 'author', 'Sorry, you cannot post')
            
    def did_create(self, instance, validated_attrs):
        inform_subscribers(instance)
```

#####serializers.py
```python
class TodoSerializer(ValidatedModelSerializer):
    class Meta:
        model = Todo
        fields = '__all__'
        validator_class = TodoValidator
```

###Example: endpoint customization
#####endpoints.py
```python
class TodoSpecialEndpoint(Endpoint):
    serializer = TodoSerializer
    config = {
        'get': {
            'queryset': lambda todo, **url: todo.objects.all(),
            'filters': {
                'hot': lambda: qs, hot: qs.filter(hot=hot),
                'confirmed': lambda: qs, confirmed: qs.filter(confirmed=confirmed)
            }
        }
    }
    
    @classmethod
    def can_get(cls):
        pre_permission = lambda request, **url: not request.user.is_anonymous
        post_permission = lambda request, queryset, attrs: not attrs.get('confirmed', False)
        return (pre_permission, post_permission)
```

###Installation
**Requirements**: this package depends on `django` and `djangorestframework`.
```
pip install django-alt
```