"""Test feed generator."""

import time
from queue import Queue
from threading import Thread
from typing import Optional
from unittest.case import TestCase

from rethinkmodel import config
from rethinkmodel.db import connect
from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from tests.utils import clean

DB_NAME = "test_feed"


class FeededUser(Model):
    """A simple user."""

    name: str
    pointer: Optional[str]


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

        queue = Queue()

        def wait_for_changes():
            feed = FeededUser.changes()
            queue.put(True)
            old, new = next(feed)
            self.assertIsNone(old)
            self.assertEqual(new.name, first_call_name)
            queue.put(True)
            old, new = next(feed)
            self.assertEqual(old.name, first_call_name)
            self.assertEqual(new.name, second_call_name)

        thread = Thread(target=wait_for_changes)
        thread.start()
        # wait for thread to be ready
        queue.get()
        time.sleep(1)
        # firs save
        user = FeededUser(name=first_call_name).save()

        # change name
        queue.get()
        time.sleep(1)
        user.name = second_call_name
        user.save()

        # stop
        thread.join()

    def test_with_filter(self):
        """Test to get a feed with a filter."""
        queue = Queue()

        def filter_user():
            feed = FeededUser.changes(select=lambda res: res["name"].eq("foo"))
            queue.put(True)
            # feed = FeededUser.changes()
            old, new = next(feed)
            self.assertIsNone(old)
            if "foo" not in new.name:
                self.fail(
                    f"The object should only contain 'foo' in name, get {new.name}"
                )

        thread = Thread(target=filter_user)
        thread.start()
        queue.get(True)
        FeededUser(name="bar1").save()  # fail if it's captured
        FeededUser(name="foo").save()  # should be ok
        thread.join()


class FeedOnDeletedTest(TestCase):
    """Make test on deleted objects."""

    def setUp(self) -> None:
        """Use soft deletion."""
        config(dbname=DB_NAME, soft_delete=True)
        return super().setUp()

    def test_on_solft_deleted(self):
        """Make test on a deleted feeduser."""
        queue = Queue()

        def filter_user():
            feed = FeededUser.changes(select=lambda res: res["name"].eq("foo"))
            queue.put(True)
            old, new = next(feed)
            if "foo" not in new.name and new.pointer is not None:
                self.fail(
                    f"The object should only contain 'foo' in name and "
                    f"pointer to None, get {new.name} and {new.pointer}"
                )

            # also try on old value, in case of...
            if old and "foo" not in old.name and old.pointer is not None:
                self.fail(
                    f"The object should only contain 'foo' in name and "
                    f"pointer to None, get {new.name} and {new.pointer}"
                )

        # the deleted user
        user = FeededUser(name="bar").save()
        kept = user.id
        user.delete()

        # prepare connection
        rdb, conn = connect()

        thread = Thread(target=filter_user)
        thread.start()
        # wait for thread to be ready
        queue.get()
        time.sleep(1)

        # this will fail if the object is catched
        rdb.table(FeededUser.tablename).get(kept).update(
            {"name": "foo", "pointer": "changed"}
        ).run(conn)

        # to close the thread
        time.sleep(1)
        FeededUser(name="foo").save()
        thread.join()

        conn.close()
