#django-alt version changelog

###0.40
 - Option to validate individual fields. This allows even more separation
 of concerns. Now serializer calls `check_<field>` on the model validator for each
 `<field>` defined on the serializer (only if its value was in `attrs`).
 This validation happens *after* `base` validation is completed. Note that at this stage
 the `attrs` dict is **not** mutated.

###0.30
 - Added `fields_from_url` parameter to endpoint `config`. Until now  
 serializer fields were only specified in request body. This allows a structured and
  straightforward way to retrieve their values from URL parameters.
 - Added `recipes.md` document that aims to provide short self&ndash;explanatory 
 code excerpts.
 useful for quick scenario look-up (think *cheat&ndash;sheet*).

###0.24
 - Added shortcuts `if_all_in` and `if_any_in`.

###0.23
 - Added `coal` null-coalescing shortcut.
 - Updated `validate` attrs replacement behaviour.
 
###0.22
 - Added `serializer` back-reference to abstract validator.
 - Updated `validate` method to replace `attrs` reference, if a new object is returned from validator methods.
 - Fixed appending dot after an exclamation mark in `make_error` function.
 
###0.21
- `tests` folder renamed to `django_alt_tests` to avoid clashes. 

###0.2
- Full implementation of `Endpoint`, `Validator` and `ValidatedSerializer` interfaces.
- Initial test coverage for project.

###0.1
 - Initial version containing the basic file structure.
