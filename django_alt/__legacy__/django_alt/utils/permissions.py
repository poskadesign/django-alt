def pre_logged_in(request, **_):
    return not request.user.is_anonymous()