#django-alt version changelog

###0.61
 - Introduced `ValidatedManager` that allows validate data before 
 creating a new model instance.
 - Introduced wildcard cleaners: similarly to wildcard field validators, cleaners are
 are `clean_<field_name>` functions that are expected to return a cleaned value
 for the field. The return value is then set on the `attrs` `dict`.
 - Shortcut `coal_first` renamed to a more memorable `first_defined`.
 - Improved test coverage.

###0.60
 - Improved documentation (`readme.md`, `recipes.md`), added `indepth.md`.
 - Introduced wildcard validators: ability to defined arbitrary functions
 to validate individual fields or all attributes collectively. More information
 on this in `indepth.md`.
 - Introduced automatic query parameter casting (e.g. where possible `"1"` -> `1`, 
 `"true"` -> `True`, etc.). This feature can be turned off by adding
 `no_url_param_casting` in the config dict on the endpoint.
 - Broadened `pre_permission` and `post_permission` definition to include
 absolute values instead of callables:
    - `True`  -> permission always granted,
    - `False` -> permission never granted,
    - `None`  -> no permission needed (`True` <=> `None`, the distinction is only semantic).
 - Added `ValidatedModelListSerializer`.
 - Added `coal_first` shortcut function. It finds the first argument 
 that is not `None` and doesn't raise a `KeyError`.
 - Added `compose_and` shortcut. It composes an iterable of callables 
 with identical signatures and asserts universal quantification for their results.
 - Added `pre_logged_in` permission shortcut.

###0.50
 - In addition to individual field validation, it is now possible to define
 own methods on the `Validator` that are automatically called upon create/update.
 The rules of custom function definition on `Validator` is as follows:
  - `field_<field_name>` if defined, these functions are called for each serializer field. 
  These functions accept one parameter &ndash; `value` (the given field's value).
  - `check_*` any defined function starting with `check_` is called automatically in an
     alphabetical order after `base` validation. These functions accept one
     parameter &ndash; `attrs` dict.
  - It is also worthwhile to know that `check_*` functions **should not** mutate the
   attrs object

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
