#django-alt version changelog

###0.3
 - added `fields_from_url` parameter to endpoint `config`. Until now  
 serializer fields were only specified in request body. This allows a structured and
  straightforward way to retrieve their values from URL parameters.
 - added `recipes.md` document that aims to provide short self&ndash;explanatory 
 code excerpts.
 useful for quick scenario look-up (think *cheat&ndash;sheet*).

###0.24
 - added shortcuts `if_all_in` and `if_any_in`.

###0.23
 - added `coal` null-coalescing shortcut.
 - updated `validate` attrs replacement behaviour.
 
###0.22
 - added `serializer` back-reference to abstract validator.
 - updated `validate` method to replace `attrs` reference, if a new object is returned from validator methods.
 - fixed appending dot after an exclamation mark in `make_error` function.
 
###0.21
- `tests` folder renamed to `django_alt_tests` to avoid clashes. 

###0.2
- Full implementation of `Endpoint`, `Validator` and `ValidatedSerializer` interfaces.
- Initial test coverage for project.

###0.1
 - Initial version containing the basic file structure.
