""" Test basic usage of rethinkmodel """
# pylint: disable=too-few-public-methods,missing-class-docstring
import sys
from datetime import datetime
from unittest import TestCase

# try/except because some IDE complains about bad imports
try:
    from rethinkdb import errors
    from rethinkmodel import Model, config, manage
    from rethinkmodel.checkers import NonNull, Unique
    from rethinkmodel.db import connect
    from rethinkmodel.exceptions import (BadType, NonNullException,
                                         UniqueException, UnknownField)
except ImportError as imp:
    print(imp)
    sys.exit(1)

DB_NAME = "test_standard_useage"
config(dbname=DB_NAME)


class User(Model):
    """ A tiny minimal user """

    username: str


class StrongerUser(Model):
    """ A user wih Unique field on username """

    __tablename__ = "users2"
    username: (str, Unique)


class WithNotNone(Model):
    """ A simple objet with non null attribute """

    username: (str, NonNull)


# initialte database
rdb, conn = connect()
try:
    rdb.db_drop(DB_NAME).run(conn)
except errors.ReqlOpFailedError as error:
    print(error)


class DatabaseTests(TestCase):
    """ RethinkDB Model tests """

    def setUp(self):
        manage.check_db()
        manage.manage(__name__)

    def test_bad_type(self):
        """ Test create object with bad type """
        with self.assertRaises(BadType):
            _ = User(username=42)

    def test_dates(self):
        """ Test date injection """
        user = User(username="the date user")
        user.save()
        now = datetime.now()

        # create
        self.assertIsInstance(user.created_at, datetime)
        self.assertIsNone(user.updated_at)
        self.assertIsNone(user.deleted_at)
        self.assertEqual(user.created_at.day, now.day)
        created = user.created_at
        # update
        user.save()
        self.assertIsInstance(user.created_at, datetime)
        self.assertEqual(created, user.created_at)  # creation data must not change
        self.assertIsInstance(user.updated_at, datetime)
        self.assertIsNone(user.deleted_at)

        # whith get
        fetch = User.get(user.id)
        self.assertIsInstance(fetch.created_at, datetime)
        self.assertEqual(fetch.created_at.day, now.day)

    def test_not_declared_field(self):
        """ Test create an object with not declared field """
        with self.assertRaises(UnknownField):
            _ = User(foo="bar")

    def test_save_and_get(self):
        """ Check if save method works and to get saved object """
        user = User(username="foo")
        user.save()
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "foo")

        saved = User.get(user.id)
        self.assertEqual(saved.id, user.id)
        self.assertEqual(saved.username, user.username)

    def test_update(self):
        """ Test to update an username """
        user = User(username="before")
        user.save()

        user.username = "after"
        user.save()

        before = User.filter({"username": "before"})
        self.assertIsNone(before)

        after = User.filter({"username": "after"})
        self.assertIsNotNone(after)
        self.assertEqual(after[0].id, user.id)

    def test_unicity(self):
        """ Check if Unique annotation works """
        user = StrongerUser(username="foo")
        user.save()

        user2 = StrongerUser(username="foo")
        with self.assertRaises(UniqueException):
            user2.save()

    def test_touch_property(self):
        """ Try to touch property with good and bad typed values """
        user = User(username="Alice")
        user.username = "Bob"
        self.assertEqual(user.username, "Bob")

        with self.assertRaises(BadType):
            user.username = 42

    def test_non_null_annotation(self):
        """ Check if NonNull attribute raises exception """

        nnobj = WithNotNone(username="foo")
        with self.assertRaises(NonNullException):
            nnobj.username = None
            nnobj.save()

    def test_delete_object(self):
        """ Try to delete from classmethod and object method """

        # use object method "delete"
        user = User(username="removeme")
        user.save()
        uid = user.id

        user.delete()

        fetch = User.get(uid)
        self.assertIsNone(fetch)

        # use classmethod "delete_id"
        user2 = User(username="removethisalso")
        user2.save()

        User.delete_id(user2.id)

        fetch = User.get(user2.id)
        self.assertIsNone(fetch)
