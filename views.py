
import logging
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import redirect
from . import api

logger = logging.getLogger(__name__)


def login_view(request):
    txt = '<a href="{}">Signup with your Reddit account</a>'
    url = api.make_authorization_url(request)
    return HttpResponse(txt.format(url))


def logout_view(request):
    api.delete_token(request)
    return redirect('/')


def reddit_callback_view(request):
    """Reddit oAuth redirects here after auth."""
    logger.info("Reddit API returned.")
    if request.GET.get('error', None):
        return "Error: " + request.GET['error']
    if not api.is_valid_state(request):
        return "Error: incorrect state value."
    logger.info("No error and valid state returned.")

    if api.get_token(request):
        # Got an access_token from Reddit, now login the user locally.
        logger.info("Received valid access_token.")
        reddit_user = api.get_user(request)

        if not reddit_user:
            # Reddit didn't return a user object, something went wrong.
            logger.info("Invalid reddit_user returned.")
            return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
        logger.info("Received valid reddit_user: '%s'", reddit_user['name'])
        # This will authenticate an existing user and create a new user
        # if necessary.
        user = authenticate(reddit_user=reddit_user['name'])

        if user is None:
            # Return an 'invalid login' error message.
            logger.info("Local user could NOT be authenticated.")
            return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
        else:
            logger.info("Local user authenticated as: '%s'", user.username)
            if user.is_active:
                logger.info("Local user is active, login...")
                login(request, user)
                logger.info("Logged in, all done. Redirect...")
                return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_SUCCESS)
            else:
                # Return a 'disabled account' error message
                logger.info("Error, local user set to 'inactive'.")
                return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
    else:
        # No access_token received, maybe the user denied access.
        logger.info("Invalid access_token.")
        return redirect(settings.OAUTH_REDDIT_REDIRECT_AUTH_ERROR)
