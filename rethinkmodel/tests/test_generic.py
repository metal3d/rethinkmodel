""" Some Generic tests """
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
    name: Optional[str]

    @classmethod
    def get_indexes(cls):
        return ["name"]


class Gallery(Model):
    name: Optional[str]


class Matrix(Model):
    name: Optional[str]


class LongNameTable(Model):
    __tablename__ = "long"


class LogEvent(Model):
    name: Optional[str]

    def on_created(self):
        logging.getLogger(LOGGER_NAME).info("event created")

    def on_deleted(self):
        logging.getLogger(LOGGER_NAME).info("event deleted")

    def on_modified(self):
        logging.getLogger(LOGGER_NAME).info("event modified")


utils.clean("test_generic")


class GenericTest(unittest.TestCase):
    def setUp(self) -> None:
        config(dbname="test_generic")
        manage(__name__)
        return super().setUp()

    def test_generate_tablename(self):
        """ Check if automatic name is OK """

        self.assertEqual(User.tablename, "users")
        self.assertEqual(Gallery.tablename, "galleries")
        self.assertEqual(Matrix.tablename, "matrices")
        self.assertEqual(LongNameTable.tablename, "long")

    def test_todict(self):
        """ Object should be well shaped in dict """
        name = "Create user"
        user = User(name=name)
        check = user.todict()
        self.assertDictEqual(
            check,
            {
                "id": None,
                "created_at": None,
                "deleted_at": None,
                "updated_at": None,
                "name": name,
            },
        )

    def test_create(self):
        """ Try to inject data in database """

        user = User(name="Create user")
        user.save()
        self.assertIsNotNone(user.id)

    def test_filter(self):
        """ Test filtering data """
        user = User(name="Filtered")
        user.save()

        filtered = User.filter({"name": user.name})
        self.assertTrue(len(filtered) != 0)
        self.assertEqual(filtered[0].id, user.id)
        self.assertEqual(filtered[0].name, user.name)

    def test_attribute_error(self):
        """ Check if badly named attribute raises exception """
        with self.assertRaises(AttributeError):
            _ = User(foo="bar")

    def test_get_all(self):
        """ Test getting all object with or whithout limit """
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
        """ Test create, update, delete and associated events """
        log = LogEvent(name="Log Object")

        with self.assertLogs(LOGGER_NAME) as logevent:
            log.save()
            self.assertTrue("event created" in "".join(logevent.output))
        with self.assertLogs(LOGGER_NAME) as logevent:
            log.name = "Log Object is modified"
            log.save()
            self.assertTrue("event modified" in "".join(logevent.output))
        with self.assertLogs(LOGGER_NAME) as logevent:
            log.delete()
            self.assertTrue("event deleted" in "".join(logevent.output))
            self.assertIsNone(log.id)
