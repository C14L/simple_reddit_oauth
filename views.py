
from . import api
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import redirect


def login_view(request):
    txt = '<a href="{}">Signup with your Reddit account</a>'
    url = api.make_authorization_url(request)
    return HttpResponse(txt.format(url))


def logout_view(request):
    api.delete_token(request)
    return redirect('/')


def reddit_callback_view(request):
    """Reddit oAuth redirects here after auth."""
    pfx = "--> reddit_callback_view() --> "
    print(pfx + "Reddit API returned.")
    if request.GET.get('error', None):
        return "Error: " + request.GET['error']
    if not api.is_valid_state(request):
        return "Error: incorrect state value."
    print(pfx + "No error and valid state returned.")

    if api.get_token(request):
        # Got an access_token from Reddit, now login the user locally.
        print(pfx + "Received valid access_token.")
        reddit_user = api.get_user(request)

        if not reddit_user:
            # Reddit didn't return a user object, something went wrong.
            print(pfx + "Invalid reddit_user returned.")
            return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
        print(pfx + "Received valid reddit_user: '{}'".format(
            reddit_user['name']))
        # This will authenticate an existing user and create a new user
        # if necessary.
        user = authenticate(reddit_user=reddit_user['name'])

        if user is None:
            # Return an 'invalid login' error message.
            print(pfx + "Local user could NOT be authenticated.")
            return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
        else:
            print(pfx + "Local user authenticated as: '{}'".format(
                user.username))
            if user.is_active:
                print(pfx + "Local user is active, login...")
                login(request, user)
                print(pfx + "Logged in, all done. Redirect...")
                return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_SUCCESS)
            else:
                # Return a 'disabled account' error message
                print(pfx + "Error, local user set to 'inactive'.")
                return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
    else:
        # No access_token received, maybe the user denied access.
        print(pfx + "Invalid access_token.")
        return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
