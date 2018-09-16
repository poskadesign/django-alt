![logo]

-----

django-alt is an alternative approach to data validation and 
REST endpoint definition in Django and DRF.

**Development branch**

### Installation
**Requirements**: this package depends on `django`, `djangorestframework` and `typing` packages.
```
pip install django-alt
```

### Motives
- No standardized way to separate *domain* and *data* logic.
- No standardized way to validate serialized data.
- Standard validation techniques do not offer any mechanisms for *separation of concerns*. 
(e.g. validating object creation vs. update).
- Cumbersome lifecycle hooks (e.g. code to execute upon object creation).
- Allow more declarative expressions while making it easy to *spice* them up.

### Solution

This package aims to help solving these problems. It allows a notion of a
`validator` &ndash; an encapsulation of domain logic for a given model.
Validators allow you to:
 - Handle before and after lifecycle events of model changes (creation, update, deletion).
 - Write arbitrary methods to clean and validate individual fields that are automatically called when needed.
 - Write arbitrary methods to validate interdependent fields.
  
This package also includes `managers` and `endpoints` &ndash; means to automate 
validated model object management as REST resources (or not). A plentiful of
shorthand helpers make validating CRUD ops feel like a breeze. Validators also easily tie into existing infrastructure. 
 
Be sure to also 
checkout [`recipes.md`](https://github.com/poskadesign/django-alt/blob/master/docs/recipes.md) 
for quick&ndash;starting and more examples
or [`indepth.md`](https://github.com/poskadesign/django-alt/blob/master/docs/indepth.md)
for a *deeper dive*.

### Example: Todo list 
##### endpoints.py
```python
class TodoEndpoint(Endpoint):
    serializer = TodoSerializer
    config = {
        'get, patch, delete': {
            'queryset': lambda todo, **url: todo.objects.get(id=url['pk'])
        }
    }
```
##### validators.py
```python
class TodoValidator(Validator):
    def clean(self, attrs):
        attrs['slug'] = slugify(attrs['name'])
        
    def clean_author(self, author):
        return author.capitalize()
        
    def field_author(self, author):
        invalid_if(not author.is_active, 'author', 'Sorry, you cannot post')
            
    def did_create(self, instance, validated_attrs):
        inform_subscribers(instance)
```

##### serializers.py
```python
class TodoSerializer(ValidatedModelSerializer):
    class Meta:
        model = Todo
        fields = '__all__'
        validator = TodoValidator
```

### Example: endpoint customization
##### endpoints.py
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

### Notes
While on the **0.x** track, this project is subject to rapid
development and some changes might break reverse&ndash;compatibility.
Any contribution or ideas are welcome!

### Author & License
Vilius Poška.  
This project is freely licensed under the MIT license.  

[logo]: docs/logo-small.png "django-alt logo"
