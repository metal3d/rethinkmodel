""" Test basic usage of rethinkmodel """
# pylint: disable=too-few-public-methods,missing-class-docstring
import sys
from unittest import TestCase

# try/except because some IDE complains about bad imports
try:
    from rethinkdb import errors
    from rethinkmodel import Model, config, manage
    from rethinkmodel.db import connect
    from rethinkmodel.transforms import Linked
except ImportError as imp:
    print(imp)
    sys.exit(1)

DB_NAME = "test_linked_object"
config(dbname=DB_NAME)


class User(Model):
    """ A tiny minimal user """

    username: str


class Project(Model):
    name: str
    user: (User, Linked)


class ProjectNoLinked(Model):
    """ A project with no Link """

    __tablename__ = "projects2"
    name: str
    user: User


class Product(Model):
    """ A simple product with name and price """

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


class LinkedObjectTests(TestCase):
    def setUp(self):
        manage.check_db()
        manage.manage(__name__)

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

        user = User(
            username="owner not linked"
        )  # do not save user, it's a nested object

        # Project2 must write the full user (not Linked annotation)
        proj2 = ProjectNoLinked(name="project2 project with not linked user", user=user)
        proj2.save()

        res = rdb.db(DB_NAME).table(ProjectNoLinked.tablename).get(proj2.id).run(conn)

        self.assertTrue("user" in res)
        self.assertIsInstance(res["user"], dict)
        self.assertEqual(res["user"]["username"], user.username)

        # for propoer representation, the nested objects should not have
        # meta data for creation, update and deletion dates
        self.assertFalse("created_at" in res["user"])
        self.assertFalse("updated_at" in res["user"])
        self.assertFalse("deleted_at" in res["user"])

        # and for this object, we need to be sure that the user is
        # back again
        self.assertDictEqual(proj2.user.todict(), user.todict())

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

        # ensire that database cnotains a full object, and not
        # links
        res = rdb.table(Bill.tablename).get(bill.id).run(conn)
        for idx, prod in enumerate(res.get("products", [])):
            self.assertIsInstance(prod, dict)
            self.assertEqual(prod["name"], products[idx].name)

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
