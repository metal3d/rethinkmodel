"""Make test on boolean filters."""
from typing import Type
from unittest.case import TestCase, skip

from rethinkmodel import config
from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from tests.utils import clean

DB_NAME = "test_boolean"


class User(Model):
    """A simple user class to make tests."""

    name: Type[str]


clean(DB_NAME)


class FilterTests(TestCase):
    """Make tests on OR and AND queries."""

    def setUp(self) -> None:
        """Set up database and table creation."""
        config(dbname=DB_NAME)
        manage(__name__)
        return super().setUp()

    def test_lambda_filter1(self):
        """Test lambda."""
        User.truncate()
        for idx in range(4):
            User(name=f"user{idx}").save()

        filtered = User.filter(
            select=lambda res: res["name"].eq("user0").or_(res["name"].eq("user2")),
            order_by="name",
        )
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].name, "user0")
        self.assertEqual(filtered[1].name, "user2")

    @skip("Probably a RethinkDB bug")
    def test_lambda_filter2(self):
        """Test lambda 2."""
        User.truncate()
        for idx in range(4):
            User(name=f"user{idx}").save()

        filtered = User.filter(
            select=lambda res: res["name"] == "user0" or res["name"] == "user2",
            order_by="name",
        )
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].name, "user0")
        self.assertEqual(filtered[1].name, "user2")
