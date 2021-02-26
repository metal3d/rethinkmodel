""" Model definition

Each data object **must** inherit from :code:`Model` class and contains
some annotations to define the types. Types can be "simples" or "Model" children.

Each Model has got:

- id: that is set from database (None by default)
- created_at: the creation date of the data (never changed)
- updated_at: the modification date, change each time you save the model
- deleted_at: if you set `soft_delete` in configuration, so the model is \
              never deleted but this date is set. \
              RethinkModel will filter objects to not get \
              soft deleted objects

.. note::

    When you call :code:`save()` method, the type of each field is checked,
    transformed and possibles actions are launched. Please take a look on
    Checkers, Transforms and Actions documentation.

.. code-block::

    class User(Model):
        username: Type[str]
        tags: List[str]

    class Project(Model):
        owner: Type[User]  # bind an User id here
        name: Type[str] # other field
        comment: Optional[str] # optional means that "None" is accepted


To get Linked objects, it's possible to use "join()" method

.. code-block::

    user_id = "..."
    user = User.join(user_id, Project)
    # user.projects is set by the Model

You can only set one Model in annotation. But you can set multiple Checkers,
Transforms and Actions.
"""
from datetime import datetime
from typing import Any, Optional, Type, get_args, get_type_hints

from . import db
from .db import connect


class BaseModel:  # pylint: disable=too-few-public-methods
    """ Base Model interface """

    id: Optional[str]
    created_at: Optional[datetime]
    deleted_at: Optional[datetime]
    updated_at: Optional[datetime]


class Model(BaseModel):
    """ Model is the parent class of all tables for RethinkDB """

    def __init__(self, **kwargs):
        """ Construct the object with checks on types in annotations """
        # we must have ID
        self.id = None  # pylint: disable=invalid-name

        # keep connection
        self.__r, self.__conn = connect()

        # default properties
        self.created_at = None
        self.updated_at = None
        self.deleted_at = None

        annotations = get_type_hints(self.__class__).keys()

        # and then, for given parameters...
        for name, value in kwargs.items():
            # see __setattr__ which calls __validate()
            if name not in annotations and name != "id":
                raise AttributeError(
                    f"The field named {name} is not declared in {self.__class__.__name__}"
                )
            setattr(self, name, value)

    @classmethod
    @property
    def tablename(cls) -> str:
        """Get the tablename, generated if not provided
        in __tablename__ attributes"""
        try:
            tablename = getattr(cls, "__tablename__").lower()
        except AttributeError:
            tablename = cls.__name__.lower()

            # pluralize name
            if tablename[-1].isnumeric():
                # it's a number, do not pluralize
                return tablename

            if tablename[-1] == "x":
                tablename = tablename[:-1] + "ces"
            elif tablename[-1] == "y":
                tablename = tablename[:-1] + "ies"
            elif tablename[-1] != "s":
                tablename += "s"

        return tablename

    def todict(self) -> dict:
        """ Return dict that can be written in db """

        annotations = get_type_hints(self.__class__)

        # get only annotated attributes
        data = {k: getattr(self, k) for k in annotations.keys()}
        for name, val in data.items():
            if isinstance(val, Model):
                data[name] = val.id

        # set the id if it exists
        if self.id:
            data["id"] = self.id
        return data

    def save(self) -> Any:
        """ Insert or update data if self.id is set """
        now = datetime.astimezone(datetime.now())
        if self.id:
            self.updated_at = now
            data = self.todict()
            res = (
                self.__r.table(self.tablename)
                .get(self.id)
                .update(data)
                .run(self.__conn)
            )
        else:
            self.created_at = now
            data = self.todict()
            del data["id"]
            res = self.__r.table(self.tablename).insert(data).run(self.__conn)
            self.id = res.get("generated_keys")[0]
        return self

    @classmethod
    def get(cls, uid: Optional[str]) -> Any:
        """ Return the correct model object """

        if db.SOFT_DELETE:
            # filter method alreadu manage soft_delete attribute, use it:
            result = cls.filter({"id": uid})
            if result and len(result) > 0:
                return result[0]
            return None

        rdb, conn = connect()
        result = rdb.table(cls.tablename).get(uid).run(conn)
        conn.close()

        if not result:
            return None

        return cls.__build(result)

    def delete(self):
        """ Delete this object from DB """
        if db.SOFT_DELETE:
            self.__r.table(self.tablename).get(self.id).update(
                {"deleted_at": datetime.astimezone(datetime.now())}
            ).run(self.__conn)
        else:
            self.__r.table(self.tablename).get(self.id).delete().run(self.__conn)

    @classmethod
    def delete_id(cls, idx=None):
        """ Delete the object that is identified by "id" """

        if idx is None:
            return
        data = cls.__build({})
        data.id = idx
        data.delete()

    @classmethod
    def __build(cls, result: dict):
        """ Build the object with nested object if there's Linked attributes """

        return cls(**result)

    @classmethod
    def filter(cls, select: dict = None) -> list:
        """ Select object in database with filters """

        # force not deleted object
        if db.SOFT_DELETE:
            select["deleted_at"] = None
        rdb, conn = connect()
        results = rdb.table(cls.tablename).filter(select).run(conn)
        conn.close()
        if hasattr(results, "items") and len(results.items) > 0:
            return [cls.__build(u) for u in results]

        return []

    def join(self, *models: Type[BaseModel]) -> object:
        """ Join linked models to the current model, fetched by id """
        for model in models:
            if not issubclass(model, Model):
                continue

            # find the right attribute in "self" that is bounded to "model"
            hints = get_type_hints(model)
            for name, hint in hints.items():
                args = get_args(hint)
                if self.__class__ in args:
                    fields = model.filter({name: self.id})
                    setattr(self, model.tablename, fields)

        return self

    def __del__(self):
        try:
            self.__conn.close()
        finally:
            pass
