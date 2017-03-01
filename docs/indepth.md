#django-alt in depth

A more involved reference of the package.
###Structure

![package]

The figure above describes the three usual methods of using this package.
 - **Method 1** allows to encapsulate domain logic in the `Validator` and
 manually call it's functions for a `dict` containing its destined model's
 attributes.
 - **Method 2** automates the model's attribute `dict` generation by 
 serializing the data from which the object is to be constructed. It also
 works the other way: the `Serializer` takes a model instance and serializes
 it to `dict`, allowing to manipulate it in the `Validator` when outputting
 the object.
 - **Method 3** takes a step further. It allows to concisely create views
 (or more specifically viewsets) that connect to serializers and automate
 object CRUD operations. This method also allows to easily and reusably
 define model/object level permissions. Every piece of the puzzle aims to
 be trivial to customize and plug-in/out.
 

###Validator
```python
class Validator:
    def __init__(self, *, model=None, serializer=None, **context): pass
``` 

Basic principle: 
 - data comes in, 
 - data is manipulated/checked/validated, 
 - errors/data comes out.
 
`Validator` subclasses take care of this. If used with a 
`ValidatedModelSerializer`, the serializer automatically 
handles the execution of its functions. These are the functions that
 can (should) be subclassed.

----------------------
##### Field cleaning 
```python
def clean(self, attrs: dict) -> Union[dict, None]: pass
```
Base clean method. Executed before base validation. Use this for
- value cleaning (lowercasing, normalization, etc.);
- setting or generating default dependent values (like slugs).

----------------------
##### Field validation
```python
def base(self, attrs: dict) -> Union[dict, None]: pass
```
Executed before create and update methods. Use this for
- raising validation errors independent from create or update.

----------------------
```python
def base_db(self, attrs: dict) -> Union[dict, None]: pass
```
Executed as last step of validation. As DB access can be considered 
expensive, this will run last, provided any other steps check out. Use this for
- validation that requires database access;
- validation logic that is more time/resource consuming.

----------------------
##### Lifecycle hooks: `will_*`
```python
def will_create(self, attrs: dict) -> Union[dict, None]: pass
```
Called when a new instance is created from `attrs`. Use this for
- placing validation logic that should be executed solely on record creation.

----------------------
```python
def will_update(self, instance, attrs: dict) -> Union[dict, None]: pass
```
Called when an existing instance is populated with new `attrs`.
`instance` parameter &ndash; existing instance to be updated.
Use this for
- placing validation logic that should be solely executed on record update.

----------------------
```python
def will_delete(self, queryset) -> None: pass
```
Called before a queryset is deleted. Parameter `queryset` &ndash; items to be deleted.

----------------------
##### Lifecycle hooks: `did_*`
```python
def did_create(self, instance, validated_attrs: dict) -> None: pass
```
Called after a model instance is created. 
 - `instance` &ndash; the created model instance;
 - `validated_attrs` &ndash; validated attributes used to create the instance.
 
----------------------
```python
def did_update(self, instance, validated_attrs: dict) -> None: pass
```
Called after a model instance is updated. 
 - `instance` &ndash; the updated model instance;
 - `validated_attrs` &ndash; validated attributes used to update the instance.
 
----------------------
```python
def did_update(self, attrs: dict) -> None: pass
```
Called after a model instance is deleted.
 - `attrs` &ndash; attributes passed from the request object;
 
----------------------
##### Presentation control
```python
def to_representation(self, repr_attrs: OrderedDict, validated_attrs: dict = None) -> OrderedDict: pass
```
Called when a queried object is transformed to a `dict` 
of primitives by underlying DRF. Use this for
- post-processing display values before converting them to JSON.


- `repr_attrs` &ndash; an `OrderedDict` that is composed by DRF;
- `validated_attrs` &ndash; a `dict` containing attributes that 
were passed through validation functions;
- *returns* modified repr_attrs OrderedDict.

----------------------
##### Wildcard checkers
These are arbitrary functions that can be defined on the validator and
are automatically called by the serializer on occasions.

```python
def field_<name>(self, value) -> None: pass
```
 If subclass defines functions named `field_<name>` where 
 `name` corresponds to a field declared on the serializer, 
 executes such functions with the field's value as the parameter. 
 The function **should not** mutate anything &ndash; 
 only raise `ValidationError` in the case of invalid field value.  
 `field_` execution is done by the `validate_extras` function on 
 the serializer.
 
----------------------
```python
def check_<what>(self, value) -> None: pass
```
 If subclass defines functions with names starting with `check_`,
 executes such functions with attrs dict as the parameter.
 All functions are called in alphabetical order.
 Again, the function **should not** mutate anything. It is used to
 fields that are dependent on one another.   
 `check_` execution is done by the `validate_checks` function on 
 the validator.


[package]: package-composition.png "django-alt composition"
