""" RethinkDB Model

The standard method to use this package is to import Model and optionally
some Transform and Checker. Then you can create a class extending the Model:

.. code-block::

    class User(Model):
        name: (str, Unique, NonNull)
        password: (str, NonNull)
        email: str
        age: int

    user = User(
        name="foo",
        password="secret",
        email="me@domain",
        age=42
    )
    # save the object in database
    u.save()

Now, "user" object is saved in database, **its "id" property is now set** and the
next "save()" call will **update** the object instead of creating a new one.

"""
import os

from rethinkdb import RethinkDB

from . import db
from .checkers import Checker, NonNull, Unique
from .db import connect
from .exceptions import (BadType, NonNullException, UniqueException,
                         UnknownField)
from .transforms import Linked, Transform

__version__ = "0.0.1"


def config(  # pylint: disable=too-many-arguments
    user=db.USER,
    password=db.PASSWORD,
    host=db.HOST,
    port=db.PORT,
    dbname=db.DB_NAME,
    timeout=db.TIMEOUT,
    ssl=db.SSL,
):
    """Configure database connection

    This **must** be called **before** any Model method call !
    """
    db.USER = user
    db.PASSWORD = password
    db.HOST = host
    db.PORT = port
    db.DB_NAME = dbname
    db.TIMEOUT = timeout
    db.SSL = ssl


class Model:
    """ Model is the parent class of all tables for RethinkDB """

    def __init__(self, **kwargs):
        """ Construct the object with checks on types in annotations """
        # we must have ID
        self.id = None  # pylint: disable=invalid-name

        # keep connection
        self.__r, self.__conn = connect()

        annotations = self._annotations().keys()
        for name, value in kwargs.items():
            # see __setattr__ which calls __validate()
            if name not in annotations and name != "id":
                raise UnknownField(
                    f"The field named {name} is not declared in {self.__class__.__name__}"
                )
            self.__setattr__(name, value)

    @classmethod
    def _annotations(cls) -> dict:
        annotations = getattr(cls, "__annotations__")
        for name, kind in annotations.items():
            if not isinstance(kind, tuple):
                annotations[name] = (kind,)

        return annotations

    def __validate(self, **kwargs):
        # apply attribute from annotations
        annotations = self._annotations()

        for name, value in kwargs.items():
            # no need to check this, it's an automated field for us
            if name == "id":
                continue

            if name not in annotations:
                raise UnknownField(
                    f"The field named {name} is not declared in {self.__class__.__name__}"
                )

            if value is None:
                # for now, it's ok. Checkers may raise exception later
                continue

            kind = annotations[name]
            if type(value) not in kind and list not in kind:
                if Linked in kind and isinstance(value, str):
                    # in this case, the annotation says that we need to
                    # link an object with it's id, so we accept to have
                    # a string
                    # TODO: validate the id ?
                    continue
                raise BadType(
                    f'Field named "{name}" of "{self.tablename}" '
                    f"should be typed as one of "
                    f"{kind} instead of type {type(value)}"
                )

    def __setattr__(self, name, value):
        if name in self._annotations():
            # will raise exception if something goes wrong
            self.__validate(**{name: value})

        # then, keep the value in attribute
        # (we use __dict__ to avoid recursion)
        self.__dict__[name] = value

    @classmethod
    @property
    def tablename(cls):
        """Get the tablename, generated if not provided
        in __tablename__ attributes"""
        try:
            tablename = cls.__tablename__.lower()
        except AttributeError:
            tablename = cls.__name__.lower()

            # pluralize name
            if tablename[-1].isnumeric():
                # it's a number, do not pluralize
                return tablename

            if tablename[-1] == "x":
                tablename += "e"
            if tablename[-1] != "s":
                tablename += "s"

        return tablename

    def __process_checkers(self):
        """ Check fields like unicity in base, non null values... """
        annotations = self._annotations()
        for name, kinds in annotations.items():
            for kind in kinds:
                if isinstance(kind(), Checker):
                    kind.check(self, name)
        return True

    def todict(self):
        """ Return dict that can be written in db """

        annotations = self._annotations()

        # get only annotated attributes
        data = {k: getattr(self, k) for k in annotations.keys()}

        # must call "todict" on every element if it's a Model subclass
        for name, kinds in annotations.items():
            attribute = getattr(self, name)

            # a field can contain several Model
            if isinstance(attribute, list):
                objects = []
                for attr in attribute:
                    if hasattr(attr, "todict"):
                        objects.append(attr.todict())
                    else:
                        objects.append(attr)
                data[name] = objects

            # or to be a Model
            elif hasattr(attribute, "todict"):
                data[name] = attribute.todict()

            # find Transfrom annotations and apply them
            transformations = [
                transformation
                for transformation in kinds
                if issubclass(transformation, Transform)
            ]
            for transormation in transformations:
                data[name] = transormation.transform(self, name)

        # set the id if it exists
        if self.id:
            data["id"] = self.id
        return data

    def save(self):
        """ Insert or update data if self.id is set """

        # check if all attributes are ok
        self.__process_checkers()

        rdb, conn = self.__r, self.__conn

        data = self.todict()

        if self.id is not None:
            # update if the object has got an id
            del data["id"]
            res = rdb.table(self.tablename).get(self.id).update(data).run(conn)
        else:
            # insert if the object hasn't got id
            res = rdb.table(self.tablename).insert(data).run(conn)
            if res["inserted"] > 0:
                self.id = res["generated_keys"][0]
            else:
                raise Exception(res)

        return self

    @classmethod
    def get(cls, uid: str) -> object:
        """ Return the correct model object """

        rdb, conn = connect()
        result = rdb.table(cls.tablename).get(uid).run(conn)
        conn.close()

        if not result:
            return None

        return cls.__build(result)

    def delete(self):
        """ Delete this object from DB """
        self.delete_id(self.id)

    @classmethod
    def delete_id(cls, idx):
        """ Delete the object that is identified by "id" """
        assert idx is not None

        rdb, conn = connect()
        rdb.table(cls.tablename).get(idx).delete().run(conn)
        conn.close()

    @classmethod
    def __build(cls, result: dict):
        """ Build the object with nested object if there's Linked attributes """

        for name, kinds in cls._annotations().items():
            # find the type
            modelkind = [k for k in kinds if issubclass(k, Model)]
            if len(modelkind) > 0:
                modelkind = modelkind[0]

            # first, check if the attribute is a list
            if isinstance(result[name], list):
                # build the objects
                result[name] = [
                    modelkind(**data)
                    for data in result[name]
                    if not isinstance(data, Model)
                ]
            elif isinstance(result[name], dict):
                result[name] = modelkind(**result[name])

            linked = [k for k in kinds if issubclass(k, Model)]
            if len(linked) == 0:
                continue

            linked = linked[0]

            for kind in kinds:
                if issubclass(kind, Linked) and list not in kinds:
                    # we need to find the linked element
                    tofind = result[name]
                    linked = linked.get(tofind)
                    result[name] = linked

        return cls(**result)

    @classmethod
    def filter(cls, select: dict = None) -> dict:
        """ Select object in database with filters """

        rdb, conn = connect()
        results = rdb.table(cls.tablename).filter(select).run(conn)
        conn.close()
        if hasattr(results, "items") and len(results.items) > 0:
            return [cls.__build(u) for u in results]

        return None

    def __del__(self):
        try:
            self.__conn.close()
        finally:
            pass
