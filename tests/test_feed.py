"""Test feed generator."""

import time
from threading import Thread
from unittest.case import TestCase

from rethinkmodel import config
from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from tests.utils import clean

DB_NAME = "test_feed"


class FeededUser(Model):
    """A simple user."""

    name: str


clean(DB_NAME)


class FeedTest(TestCase):
    """Make some test on feed."""

    def setUp(self) -> None:
        """Manage table."""
        config(dbname=DB_NAME)
        manage(__name__)
        return super().setUp()

    def test_feed_get(self):
        """Test to detect table change."""
        first_call_name = "first"
        second_call_name = "second"

        def wait_for_changes():
            feed = FeededUser.changes()
            old, new = next(feed)
            self.assertIsNone(old)
            self.assertEqual(new.name, first_call_name)
            old, new = next(feed)
            self.assertEqual(old.name, first_call_name)
            self.assertEqual(new.name, second_call_name)

        thread = Thread(target=wait_for_changes)
        thread.start()
        time.sleep(3)  # we need to wait a bit...
        user = FeededUser(name=first_call_name).save()
        time.sleep(1)
        user.name = second_call_name
        user.save()
        thread.join()
