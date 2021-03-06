"""Handle all Reddit API calls."""

import requests
import requests.auth
from time import time as unixtime
from urllib.parse import urlencode
from uuid import uuid4
from django.conf import settings
from django.contrib.auth import logout


def get_token(request, refresh=False):
    """
    Return an access_token, either from session storage or get a
    fresh one from the Reddit API. If there is a "code" parameter
    in the request GET values, then refresh the cached access_token
    value.

    Call with refresh=True to refresh an existing access_token.
    """
    api_url = "https://ssl.reddit.com/api/v1/access_token"
    is_expired = request.session.get("expires", 0) < int(unixtime())
    headers = settings.OAUTH_REDDIT_BASE_HEADERS
    client_auth = requests.auth.HTTPBasicAuth(
        settings.OAUTH_REDDIT_CLIENT_ID, settings.OAUTH_REDDIT_CLIENT_SECRET
    )

    if is_expired and request.GET.get("code", None):
        # Received an access code to get a new access_token. Use
        # this above anything else.
        post_data = {
            "grant_type": "authorization_code",
            "code": request.GET.get("code"),
            "redirect_uri": settings.OAUTH_REDDIT_REDIRECT_URI,
        }
        response = requests.post(
            api_url, auth=client_auth, headers=headers, data=post_data
        )
        t = response.json()
        request.session["access_token"] = t.get("access_token", "")
        request.session["refresh_token"] = t.get("refresh_token", "")
        request.session["token_type"] = t.get("token_type", "")
        request.session["expires"] = int(unixtime()) + int(t.get("expires_in", 0))
        request.session["scope"] = t.get("scope", "")
        if settings.DEBUG:
            print("Initial access_token acquired.")

    elif (refresh or is_expired) and request.session.get("refresh_token", False):

        # The previous access_token is expired, use refresh_token to
        # get a new one.
        post_data = {
            "grant_type": "refresh_token",
            "refresh_token": request.session.get("refresh_token"),
        }
        response = requests.post(
            api_url, auth=client_auth, headers=headers, data=post_data
        )
        t = response.json()
        request.session["access_token"] = t.get("access_token", "")
        request.session["token_type"] = t.get("token_type", "")
        request.session["expires"] = int(unixtime()) + int(t.get("expires_in", 0))
        request.session["scope"] = t.get("scope", "")
        if settings.DEBUG:
            print("New access_token acquired.")
    else:
        if settings.DEBUG:
            if request.session.get("access_token", False):
                print("Re-using cached access_token.")
            else:
                print("No access_token found anywhere!")

    # If there is an access_token now, return it. Or wipe session vals.
    if request.session.get("access_token", False):
        return request.session.get("access_token")
    else:
        request.session["access_token"] = None
        request.session["refresh_token"] = None
        request.session["token_type"] = None
        request.session["expires"] = 0
        request.session["scope"] = None
        return False


def delete_token(request):
    logout(request)  # deletes the session access_token, etc.


def is_valid_state(request):
    """Check if we got the same "state" value back from Reddit."""
    state = request.GET.get("state", None)
    orig = request.session.get("oauth_reddit_state", None)
    return bool(state) and state == orig


def make_authorization_url(request):
    """
    Return a reddit url for oauth authentification. the url
    includes a callback url, to be redirected to after Reddit's
    authentication of the user happened. This method
    should be called from a view that uses the return url
    as a <a href> value.
    """
    api_url = "https://ssl.reddit.com/api/v1/authorize?"
    request.session["oauth_reddit_state"] = str(uuid4())
    params = urlencode(
        {
            "client_id": settings.OAUTH_REDDIT_CLIENT_ID,
            "response_type": "code",
            "state": request.session["oauth_reddit_state"],
            "redirect_uri": settings.OAUTH_REDDIT_REDIRECT_URI,
            "duration": settings.OAUTH_REDDIT_DURATION,
            "scope": settings.OAUTH_REDDIT_SCOPE,
        }
    )

    return api_url + params


def cleanup_sr_list(raw_sr_list):
    """
    Takes a raw subreddits list, as it comes from the Reddit API,
    and removes all unneeded fields and hierarchies. Returns a
    simple list of subreddit dicts.
    """
    if not raw_sr_list:
        return False
    subreddits = []
    get_fields = [
        "id",
        "url",  # sr url, e.g. "/r/de"
        "over18",  # NSFW sr
        "lang",  # sr language
        "title",  # ...
        "header_title",
        "display_name",  # ...
        "subreddit_type",  # public or private
        "subscribers",  # number of sr subscribers
        "created_utc",  # float unixtime
        "quarantine",  # ???
        "user_is_contributor",  # ...
        "user_is_moderator",  # ...
        "user_is_subscriber",  # ...
        "user_is_banned",  # ...
        "user_is_muted",  # ...
    ]
    for sr in raw_sr_list["data"]["children"]:
        x = {}
        for fi in get_fields:
            x[fi] = sr["data"][fi]
        subreddits.append(x)
    return subreddits


def _api_query_dispatch(access_token, api_url, params=None):
    response = False
    if access_token:
        headers = settings.OAUTH_REDDIT_BASE_HEADERS
        headers.update({"Authorization": "bearer " + access_token})
        response = requests.get(api_url, headers=headers, params=params)
        if settings.DEBUG:
            print("Reddit API returned status %s", response.status_code)

    return response


def api_query(request, api_url, params=None):
    access_token = get_token(request)
    response = _api_query_dispatch(access_token, api_url, params)

    if not response or response.status_code == 401:
        # Access denied! Get a fresh access_token and try again.
        access_token = get_token(request, refresh=True)
        response = _api_query_dispatch(access_token, api_url, params)

    if response and response.status_code == 200:
        return response.json()

    # Invalid access_token or status code returned.
    return False


def get_user(request):
    api_url = "https://oauth.reddit.com/api/v1/me"
    return api_query(request, api_url)


def get_trophies(request):
    api_url = "https://oauth.reddit.com/api/v1/me/trophies"
    return api_query(request, api_url)


def get_karma(request):
    api_url = "https://oauth.reddit.com/api/v1/me/karma"
    return api_query(request, api_url)


def get_sr_subscriber(request, limit=100):
    api_url = "https://oauth.reddit.com/subreddits/mine/subscriber"
    params = {"limit": limit or 100}
    response = api_query(request, api_url, params=params)

    if limit and limit <= 100:
        return cleanup_sr_list(response)

    params["limit"] = 100
    subreddits = cleanup_sr_list(response)
    count = len(subreddits)
    after = response.get("data", {}).get("after")

    while after:
        params["count"] = count
        params["after"] = after
        response = api_query(request, api_url, params=params)
        subreddits.extend(cleanup_sr_list(response))
        after = response.get("data", {}).get("after")
        count = len(subreddits)

        if limit and count >= limit:
            break

    return subreddits[:limit]


def get_sr_contributor(request):
    api_url = "https://oauth.reddit.com/subreddits/mine/contributor"
    return cleanup_sr_list(api_query(request, api_url))


def get_sr_moderator(request):
    api_url = "https://oauth.reddit.com/subreddits/mine/moderator"
    return cleanup_sr_list(api_query(request, api_url))


def get_username(access_token=None):
    user = get_user(access_token)
    return user["name"]

