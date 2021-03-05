"""Tests with soft deletion."""

from unittest.case import TestCase

from rethinkmodel import config
from rethinkmodel.db import connect
from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from tests.utils import clean

DB_NAME = "deletion_tests"


class SoftUser(Model):
    """User that is soft deleted"""

    name: str


clean(DB_NAME)


class SoftDeletionTest(TestCase):
    """Make some tests on SOFT_DELETED."""

    def setUp(self) -> None:
        """Make the connection in soft delet mode."""
        config(dbname=DB_NAME, soft_delete=True)
        manage(__name__)
        return super().setUp()

    def test_delete_and_get(self):
        """Try to save and delete object."""
        SoftUser.truncate()
        user = SoftUser(name="test 1").save()
        test = user.get(user.id)
        self.assertEqual(test.id, user.id)
        kept_id = user.id

        user.delete()
        self.assertIsNone(user.id)

        rdb, conn = connect()
        deleted = rdb.table(SoftUser.tablename).get(kept_id).run(conn)
        self.assertIsNotNone(deleted["deleted_on"])
        conn.close()

        should_fail = SoftUser.get(kept_id)
        self.assertIsNone(should_fail)

    def test_get_all(self):
        """Test to get all objects with deleted objects."""
        SoftUser.truncate()
        for i in range(3):
            SoftUser(name=f"User{i}").save()

        users = SoftUser.get_all()
        kept = users[1].id

        self.assertEqual(len(users), 3)
        users[1].delete()

        second_users = SoftUser.get_all()
        self.assertEqual(len(second_users), 2)
        for user in second_users:
            if user.id == kept:
                self.fail(f"The user id {user.id} is still fetched")
