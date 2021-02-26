""" Some Generic tests """
# pylint: disable=missing-class-docstring,too-few-public-methods

import unittest
from typing import Optional

from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from . import utils


class User(Model):
    name: Optional[str]


class Gallery(Model):
    name: Optional[str]


class Matrix(Model):
    name: Optional[str]


class LongNameTable(Model):
    __tablename__ = "long"


utils.clean("test_generic")


class GenericTest(unittest.TestCase):
    def setUp(self) -> None:
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
        user = User(name="Create user")
        check = user.todict()
        self.assertDictEqual(
            check,
            {
                "id": None,
                "created_at": None,
                "deleted_at": None,
                "updated_at": None,
                "name": "Create user",
            },
        )

    def test_create(self):
        """ Try to inject data in database """

        user = User(name="Create user")
        user.save()
        self.assertIsNotNone(user.id)

    def test_filter(self):
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
