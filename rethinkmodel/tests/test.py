""" Test basic usage of rethinkmodel """
# pylint: disable=too-few-public-methods,missing-class-docstring
import sys
from datetime import datetime
from unittest import TestCase

# try/except because some IDE complains of import
try:
    from rethinkdb import errors
    from rethinkmodel import Model, config, manage
    from rethinkmodel.checkers import NonNull, Unique
    from rethinkmodel.db import connect
    from rethinkmodel.exceptions import (BadType, NonNullException,
                                         UniqueException, UnknownField)
    from rethinkmodel.transforms import Linked
except ImportError as imp:
    print(imp)
    sys.exit(1)

DB_NAME = "test3"
config(dbname=DB_NAME)


class User(Model):
    """ A tiny minimal user """

    username: str


class User2(Model):
    """ A user wih Unique field on username """

    __tablename__ = "users2"
    username: (str, Unique)


class Project(Model):
    name: str
    user: (User, Linked)


class Project2(Model):
    __tablename__ = "projects2"
    name: str
    user: User


class WithNotNone(Model):
    username: (str, NonNull)


class Product(Model):
    name: str
    price: float


class Bill(Model):
    """ A billing process with products """

    products: (list, Product)
    client: User


class LinkedBill(Model):
    """ Same as Bill but with linked objects """

    products: (list, Product, Linked)
    client: User


# initialte database
rdb, conn = connect()
try:
    rdb.db_drop(DB_NAME).run(conn)
except errors.ReqlOpFailedError as error:
    print(error)


class DatabaseTests(TestCase):
    """ RethinkDB Model tests """

    def setUp(self):
        manage.check_db()
        manage.manage(__name__)

    def test_bad_type(self):
        """ Test create object with bad type """
        with self.assertRaises(BadType):
            _ = User(username=42)

    def test_dates(self):
        """ Test date injection """
        user = User(username="the date user")
        user.save()
        now = datetime.now()

        # create
        self.assertIsInstance(user.created_at, datetime)
        self.assertIsNone(user.updated_at)
        self.assertIsNone(user.deleted_at)
        self.assertEqual(user.created_at.day, now.day)
        # update
        user.save()
        self.assertIsInstance(user.created_at, datetime)
        self.assertIsInstance(user.updated_at, datetime)
        self.assertIsNone(user.deleted_at)

        # whith get
        fetch = User.get(user.id)
        self.assertIsInstance(fetch.created_at, datetime)
        self.assertEqual(fetch.created_at.day, now.day)

    def test_not_declared_field(self):
        """ Test create an object with not declared field """
        with self.assertRaises(UnknownField):
            _ = User(foo="bar")

    def test_save_and_get(self):
        """ Check if save method works and to get saved object """
        user = User(username="foo")
        user.save()
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "foo")

        saved = User.get(user.id)
        self.assertEqual(saved.id, user.id)
        self.assertEqual(saved.username, user.username)

    def test_update(self):
        """ Test to update an username """
        user = User(username="before")
        user.save()

        user.username = "after"
        user.save()

        before = User.filter({"username": "before"})
        self.assertIsNone(before)

        after = User.filter({"username": "after"})
        self.assertIsNotNone(after)
        self.assertEqual(after[0].id, user.id)

    def test_unicity(self):
        """ Check if Unique annotation works """
        user = User2(username="foo")
        user.save()

        user2 = User2(username="foo")
        with self.assertRaises(UniqueException):
            user2.save()

    def test_linked_object(self):
        """ Check if linked object give the linked id """
        user = User(username="the owner")
        user.save()

        proj = Project(user=user, name="The project")
        proj.save()

        # we want to be sure that "user" field is only a string
        res = rdb.db(DB_NAME).table(Project.tablename).get(proj.id).run(conn)
        self.assertEqual(res["user"], user.id)

        # get the project must make the user field to be a User object
        projget = Project.get(proj.id)
        self.assertIsInstance(projget.user, User)
        # and the id must correspond
        self.assertEqual(projget.user.id, user.id)

    def test_not_linked_object(self):
        """ Check if not linked object are well saved as dict in DB """
        user = User(username="owner not linked")
        user.save()

        # Project2 must write the full user (not Linked annotation)
        proj2 = Project2(name="project2 project with not linked user", user=user)
        proj2.save()

        res = rdb.db(DB_NAME).table(Project2.tablename).get(proj2.id).run(conn)
        self.assertIsInstance(res["user"], dict)
        self.assertEqual(res["user"]["username"], user.username)

        # and for this object, we need to be sure that the user is
        self.assertEqual(proj2.user.id, user.id)
        self.assertDictEqual(proj2.user.todict(), user.todict())

    def test_touch_property(self):
        """ Try to touch property with good and bad typed values """
        user = User(username="Alice")
        user.username = "Bob"
        self.assertEqual(user.username, "Bob")

        with self.assertRaises(BadType):
            user.username = 42

    def test_non_null_annotation(self):
        """ Check if NonNull attribute raises exception """

        nnobj = WithNotNone(username="foo")
        with self.assertRaises(NonNullException):
            nnobj.username = None
            nnobj.save()

    def test_delete_object(self):
        """ Try to delete from classmethod and object method """

        # use object method "delete"
        user = User(username="removeme")
        user.save()
        uid = user.id

        user.delete()

        fetch = User.get(uid)
        self.assertIsNone(fetch)

        # use classmethod "delete_id"
        user2 = User(username="removethisalso")
        user2.save()

        User.delete_id(user2.id)

        fetch = User.get(user2.id)
        self.assertIsNone(fetch)

    def test_list_save_get(self):
        """ Try to save an object with list """

        user = User(username="A client")

        products = [
            Product(name="object1", price=12.50),
            Product(name="object2", price=29.99),
        ]

        bill = Bill(client=user, products=products)
        try:
            bill.save()
        except Exception as error:  # pylint: disable=broad-except
            self.fail(str(error))

        # get the bill

        fetch = Bill.get(bill.id)  # bill.get is not a joke :)

        self.assertIsInstance(fetch.products, list)
        self.assertEqual(len(fetch.products), 2)
        for prod in fetch.products:
            self.assertIsInstance(prod, Product)

    def test_linked_list(self):
        """ Try to save object with Linked list """
        user = User(username="linked bill user")
        products = [
            Product(name="linked prod 1", price=42.0),
            Product(name="linked prod 2", price=9.99),
        ]
        for product in products:
            product.save()

        bill = LinkedBill(products=products, client=user)
        bill.save()
        # be sure that in database, the list is a "ID" list
        linked = rdb.table(LinkedBill.tablename).get(bill.id).run(conn)

        for idx, product in enumerate(products):
            self.assertEqual(linked["products"][idx], product.id)

        # check if objects are reconstructed
        fetch = LinkedBill.get(bill.id)
        for idx, product in enumerate(products):
            self.assertEqual(fetch.products[idx].id, product.id)
