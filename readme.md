#django-alt

django-alt is an alternative approach to data validation and 
RESTful endpoint definition in Django and DRF.

###Motives
- No standardized way to separate *domain* and *data* logic.
- No standardized way to validate serialized data.
- Standard validation techniques do not offer any mechanisms for *separation of concerns* 
(e.g. validating object creation vs. update)
- Cumbersome lifecycle hooks (e.g. code to execute upon object creation)

This package aims to solve these problems.

###Example: Todo List
#####endpoints.py
```python
class TodoListEndpoint(EndpointBase):
    serializer = TodoListSerializer
    config = {
        'get': {
            'queryset': lambda todo, **url: todo.objects.all()
        },
        'post': None
    }
```
#####validators.py
```python
class TodoValidator(ModelValidator):
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
```
