""" Test deletions with soft_delete configuration """
import sys
import unittest

try:
    from rethinkdb import errors
    from rethinkmodel import Model, config, manage
    from rethinkmodel.db import connect
except ImportError as imp:
    print(imp)
    sys.exit(1)

DB_NAME = "test_deletion"
config(dbname=DB_NAME, soft_delete=True)

# initialte database
rdb, conn = connect()
try:
    rdb.db_drop(DB_NAME).run(conn)
except errors.ReqlOpFailedError as error:
    print(error)


class User(Model):  # pylint: disable=too-few-public-methods
    """ Basic user """

    username: str


class DeletionTests(unittest.TestCase):
    """ Make some tests on soft deletion """

    def setUp(self):
        """ Prepare db and tables """
        manage.check_db()
        manage.manage(__name__)

    def test_soft_deletion(self):
        """ Try to save then SOFT delete user, and keep element in DB """
        user = User(username="user to delete")
        user.save()

        fetch = user.get(user.id)
        self.assertEqual(user.id, fetch.id)

        fetch.delete()

        deleted = user.get(fetch.id)
        self.assertIsNone(deleted)

        # check in database
        dbo = rdb.table(User.tablename).get(fetch.id).run(conn)
        self.assertIsNotNone(dbo["deleted_at"])
