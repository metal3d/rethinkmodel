""" Test cascade deletions """
# pylint: disable=too-few-public-methods
import sys
import unittest

try:
    from rethinkdb import errors
    from rethinkmodel import config, manage
    from rethinkmodel.actions import Cascade
    from rethinkmodel.db import connect
    from rethinkmodel.model import Model
    from rethinkmodel.transforms import Linked
except ImportError as imp:
    print(imp)
    sys.exit(1)

DB_NAME = "test_cascade"
config(dbname=DB_NAME)

# initialte database
rdb, conn = connect()
try:
    rdb.db_drop(DB_NAME).run(conn)
except errors.ReqlOpFailedError as error:
    print(error)


class User(Model):
    """ A simple user model """

    username: str


class Media(Model):
    """ A media can be a file for example """

    name: str


class Profile(Model):
    """ A profile can, for example, be the fixed parent of a User"""

    user: (User, Linked, Cascade)  # remove the user when we remove a profile


class Gallery(Model):
    """ A Gallery is owned by a user and contains medias """

    user: (User, Linked)  # must not be deleted
    medias: (Media, list, Linked, Cascade)  # remove medias on gallery deletion


class CascadeDeletion(unittest.TestCase):
    """ Do several tests on cascade deletion """

    def setUp(self):
        manage.check_db()
        manage.manage(__name__)

    def test_unique_deletion(self):
        """ Try to cascade delete one linked field """
        user = User(username="simple user with profile")
        profile = Profile(user=user)
        user.save()
        profile.save()

        # OK, now remove the profile, so the user should be deleted
        profile.delete()

        fetch = User.get(user.id)
        self.assertIsNone(fetch)

        # ensure that it's true in database
        fromdb = rdb.table(User.tablename).get(user.id).run(conn)
        self.assertIsNone(fromdb)

        # and in case of, try to get the profile
        fetchprofile = Profile.get(profile.id)
        self.assertIsNone(fetchprofile)

    def test_list_delettion(self):
        """ Try to delete a list of linked field """
        user = User(username="Media owner")
        user.save()

        medias = [
            Media(name="image1"),
            Media(name="image2"),
        ]
        for media in medias:
            media.save()

        gallery = Gallery(user=user, medias=medias)
        gallery.save()

        # When a gallery is deleted, we want the medias to be deleted
        gallery.delete()

        fetch = Gallery.get(gallery.id)
        self.assertIsNone(fetch)

        for media in medias:
            self.assertIsNotNone(media.id)
            self.assertTrue(len(media.id) > 0)
            getmed = Media.get(media.id)
            self.assertIsNone(getmed)
