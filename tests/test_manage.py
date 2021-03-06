"""Test manage module."""
# pylint disable=missing-class-docstring,too-few-public-methods

import unittest

from rethinkmodel import config, db
from rethinkmodel.db import connect
from rethinkmodel.manage import introspect
from rethinkmodel.model import Model

from tests import utils


class ManagedTable(Model):
    """To check if the table is well created."""

    name: str


utils.clean("test_manage")


class ManageTest(unittest.TestCase):
    """Test the manage module."""

    def setUp(self) -> None:
        """Confugure database."""
        config(dbname="test_manage")
        return super().setUp()

    def test_introspect(self):
        """Test the module introspection from path."""
        introspect(__file__)
        rdb, conn = connect()
        tables = rdb.db(db.DB_NAME).table_list().run(conn)
        conn.close()
        # the table must be created
        self.assertIn(ManagedTable.tablename, tables)
