"""Test for database."""

from unittest.case import TestCase

from rethinkdb import RethinkDB
from rethinkmodel import config
from rethinkmodel.manage import check_db


class DatabaseTest(TestCase):
    """Some tests on database creation."""

    def test_database_creation(self):
        """Check, if :meth:rethinkmodel.manage.check_db() creates the database."""
        db_name = "test_creation"
        config(dbname=db_name)
        check_db()

        rdb = RethinkDB()
        conn = rdb.connect()
        dbs = rdb.db_list().run(conn)
        if db_name not in dbs:
            self.fail("Database named {db_name} was not created")
        conn.close()
