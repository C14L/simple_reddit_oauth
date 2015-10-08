import re
from django.conf import settings
from django.test import TestCase
from .models import RedditUser


class RedditUserTestCase(TestCase):

    def test_assert_setting_reddit_api_scope_format(self):
        """
        For the "scope" value, Reddit's API uses a slight deviation
        from the oAuth 2.0 specifications, which states scopes should
        be space-separated. Reddit uses a comma separated value. Here,
        verify that the setting actually uses a comma separated list
        and NOT a standard oAuth space separated list.
        """
        self.assertEqual(
            settings.OAUTH_REDDIT_SCOPE,
            re.replace(r'[, ]+', ',', settings.OAUTH_REDDIT_SCOPE)
        )

    def test_make_authorization_url(self):
        """
        Assert that the authorization URL is constructed with all valid
        parameters.
        """
        mock_request = {'session': {}}
        url = RedditUser.make_authorization_url(mock_request)
        vals = ["scope=" + settings.OAUTH_REDDIT_SCOPE,
                "client_id=" + settings.OAUTH_REDDIT_CLIENT_ID,
                "redirect_uri=" + settings.OAUTH_REDDIT_REDIRECT_URI]
        for v in vals:
            self.assertContains(url, v)
