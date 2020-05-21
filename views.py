from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import redirect
from . import api


def login_view(request):
    txt = '<a href="{}">Signup with your Reddit account</a>'
    url = api.make_authorization_url(request)
    return HttpResponse(txt.format(url))


def logout_view(request):
    api.delete_token(request)
    return redirect('/')


def reddit_callback_view(request):
    """Reddit oAuth redirects here after auth."""
    if request.GET.get('error', None):
        return "Error: " + request.GET['error']
    if not api.is_valid_state(request):
        return "Error: incorrect state value."

    if api.get_token(request):
        # Got an access_token from Reddit, now login the user locally.
        reddit_user = api.get_user(request)

        if not reddit_user:
            # Reddit didn't return a user object, something went wrong.
            return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)

        # This will authenticate an existing user and create a new user
        # if necessary.
        user = authenticate(request, reddit_user=reddit_user['name'])

        if user is None:
            # Return an 'invalid login' error message.
            return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
        else:
            if user.is_active:
                login(request, user)
                return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_SUCCESS)
            else:
                # Return a 'disabled account' error message
                return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
    else:
        # No access_token received, maybe the user denied access.
        return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
