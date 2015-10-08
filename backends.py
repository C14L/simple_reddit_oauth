"""
Once a user is authenticated with Reddit's oAuth, this is used to
authenticate them locally and sign them in. Non-existing users are
created automatically.

See https://github.com/django/django/blob/master/django/contrib/auth/ba
ckends.py --> class RemoteUserBackend
"""

# from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import RemoteUserBackend


class RedditBackend(RemoteUserBackend):

    def authenticate(self, reddit_user):
        pfx = "--> RedditBackend.authenticate --> "
        if not reddit_user:
            return
        user = None
        username = self.clean_username(reddit_user)
        print(pfx + "Authenticate user '{}'...".format(username))
        UserModel = get_user_model()

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        user, created = UserModel._default_manager.get_or_create(
            **{UserModel.USERNAME_FIELD: username})
        if created:
            print(pfx + "User did not exist and was created.")
            user = self.configure_user(user)
            #
            # TODO: This is a new user. Fetch some additional user
            #       data from Reddit and add it to the User model.
            #       Especially the "created" (Reddit user since)
            #       field.
            #
        else:
            print(pfx + "User found.")

        print(pfx + "Returning user '{}'...".format(user.id))
        return user
