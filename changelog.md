#django-alt version changelog
###0.24
 - added shortcuts `if_all_in` and `if_any_in`
###0.23
 - added `coal` null-coalescing shortcut
 - updated `validate` attrs replacement behaviour
###0.22
 - added `serializer` back-reference to abstract validator
 - updated `validate` method to replace `attrs` reference, if a new object is returned from validator methods
 - fixed appending dot after an exclamation mark in `make_error` function
###0.21
- `tests` folder renamed to `django_alt_tests` to avoid clashes 
###0.2
- Full implementation of `Endpoint`, `Validator` and `ValidatedSerializer` interfaces
- Initial test coverage for project
###0.1
 - Initial version containing the basic file structure
