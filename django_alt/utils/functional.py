def compose_and(*functions) -> bool:
    """
    Composes an iterable of callables with identical signatures
    and asserts universal quantification for their results.
    :param functions: ant iterable of functions to call
    :return: whether all function returns evaluate to true
    """
    def func_prototype(*args, **kwargs):
        return all(f(*args, **kwargs) for f in functions)
    return func_prototype
