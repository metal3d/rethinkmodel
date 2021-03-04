"""Some Generic tests."""
# pylint: disable=missing-class-docstring,too-few-public-methods

import logging
import unittest
from typing import Optional

from rethinkmodel import config
from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from . import utils

LOGGER_NAME = "tests"


class User(Model):
    """Simple User."""

    name: Optional[str]

    @classmethod
    def get_indexes(cls):
        """Return index on `name` property."""
        return ["name"]


class Gallery(Model):
    """A Gallery."""

    name: Optional[str]


class Matrix(Model):
    """A matrix."""

    name: Optional[str]


class LongNameTable(Model):
    """Long named table."""

    __tablename__ = "long"


class LogEvent(Model):
    """To test events."""

    name: Optional[str]

    def on_created(self):
        """Call on created."""
        logging.getLogger(LOGGER_NAME).info("event created")

    def on_deleted(self):
        """Call on deleted."""
        logging.getLogger(LOGGER_NAME).info("event deleted")

    def on_modified(self):
        """Call on modified."""
        logging.getLogger(LOGGER_NAME).info("event modified")


class SimpleType(Model):
    """Simple type linked to User."""

    user: User
    name: str
    age: int


utils.clean("test_generic")


class GenericTest(unittest.TestCase):
    """Make som generic tests."""

    def setUp(self) -> None:
        """Configure database and create tables."""
        config(dbname="test_generic")
        manage(__name__)
        return super().setUp()

    def test_generate_tablename(self):
        """Check if automatic name is OK."""
        self.assertEqual(User.tablename, "users")
        self.assertEqual(Gallery.tablename, "galleries")
        self.assertEqual(Matrix.tablename, "matrices")
        self.assertEqual(LongNameTable.tablename, "long")

    def test_todict(self):
        """Object should be well shaped in dict."""
        name = "Create user"
        user = User(name=name)
        check = user.todict()
        self.assertDictEqual(
            check,
            {
                "id": None,
                "created_on": None,
                "deleted_on": None,
                "updated_on": None,
                "name": name,
            },
        )

    def test_create(self):
        """Try to inject data in database."""
        user = User(name="Create user")
        user.save()
        self.assertIsNotNone(user.id)

    def test_filter(self):
        """Test filtering data."""
        user = User(name="Filtered")
        user.save()

        filtered = User.filter({"name": user.name})
        self.assertTrue(len(filtered) != 0)
        self.assertEqual(filtered[0].id, user.id)
        self.assertEqual(filtered[0].name, user.name)

    def test_attribute_error(self):
        """Check if badly named attribute raises exception."""
        with self.assertRaises(AttributeError):
            _ = User(foo="bar")

    def test_get_all(self):
        """Test getting all object with or whithout limit."""
        User.truncate()

        # build 30 users
        _ = [User(name=f"User{i:02d}").save() for i in range(30)]

        all_users = User.get_all(order_by="name")
        self.assertEqual(len(all_users), 30)
        for i, user in enumerate(all_users):
            self.assertEqual(user.name, f"User{i:02d}")

        limited_users = User.get_all(limit=10, offset=10, order_by="name")
        self.assertEqual(len(limited_users), 10)
        for i, user in enumerate(limited_users):
            offset = i + 10
            self.assertEqual(user.name, f"User{offset:02d}")

    def test_crud_and_event(self):
        """Test create, update, delete and associated events."""
        log = LogEvent(name="Log Object")
        modified = "Log Object modified"

        with self.assertLogs(LOGGER_NAME) as logevent:
            log.save()
            self.assertTrue("event created" in "".join(logevent.output))
        with self.assertLogs(LOGGER_NAME) as logevent:
            log.name = modified
            log.save()
            self.assertTrue("event modified" in "".join(logevent.output))
            log_get = LogEvent.get(log.id)
            self.assertEqual(log_get.name, modified)
        with self.assertLogs(LOGGER_NAME) as logevent:
            last_id = log.id
            log.delete()
            self.assertTrue("event deleted" in "".join(logevent.output))
            self.assertIsNone(log.id)
            log_deleted = LogEvent.get(last_id)
            self.assertIsNone(log_deleted)

    def test_simple_types(self):
        """Should work with simple types."""
        user = User(name="simpleuser").save()
        simple = SimpleType(name="fooname", age=42, user=user)
        simple.save()

        self.assertIsNotNone(simple.id)

    def test_get_none(self):
        """Get None should not raise exception and return None."""
        user = User.get(None)
        self.assertIsNone(user)
