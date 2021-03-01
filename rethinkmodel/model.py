"""
Module to create and manage your models
=======================================

Each data object **must** inherit from :code:`Model` class and contains
some annotations to define the types. Types can be "simples" or "Model" children.

Each Model has got:

- id: that is set from database (None by default)
- created_at: the creation date of the data (never changed)
- updated_at: the modification date, change each time you save the model
- deleted_at: if you set :code:`rethinkdb.db.SOFT_DELETE` to :code:`True` \
        in configuration, so the model is \
        never deleted but this date is set. \
        Rethink:Model will filter objects to not get \
        soft deleted objects

.. code-block::

    class User(Model):
        username: Type[str] # a string, cannot be None
        tags: List[str] # a List if string, connot be None
        categories: Optional[List[str]] # list of string, can be None

        @classmethod
        def get_index(cls):
            ''' Create an index on "name" property '''
            return ['name']

    class Project(Model):
        # bind an User id here, because User is a model
        owner: Type[User]

        name: Type[str] # other field
        comment: Optional[str] # Optional => "None" is accepted


To get Linked objects, it's possible to use "join()" method

.. code-block::

    # The user will be fetched and
    # projects property is set with all 
    # related projects.
    # This is because "Project" object
    # has got a User reference field.
    user = User.get(id).join(Project)

See Model methods documentation to have a look on arguments (like limit, offset, ...)

"""
from datetime import datetime
from typing import (Any, Dict, List, Optional, Type, Union, get_args,
                    get_type_hints)

from rethinkdb import RethinkDB, errors

from . import db
from .db import connect


class BaseModel:  # pylint: disable=too-few-public-methods
    """Base Model interface

    To change the tablename and avoid name generation, you may
    use :code:`__tablename__` static property.
    """

    id: Optional[str]

    # creation date, set once the object is saved
    created_at: Optional[datetime]

    # set to the current datetime if rethinkdb.db.SOFT_DELETE is set
    deleted_at: Optional[datetime]

    # modified each time the object is saved
    updated_at: Optional[datetime]

    def on_created(self):
        """ Called after the object is created in database """

    def on_modified(self):
        """ Called after the object is modified in database """

    def on_deleted(self):
        """Called after the object is deleted from database

        .. note::

            self.id is **not** :code:None at this point. It will be set to :code:None
            after this method is called. This way, you can, for example,
            manage a cascade deletion.

        """

    @classmethod
    def get_indexes(cls) -> Optional[Union[List, Dict]]:
        """You can override this method to return a list of indexes.
        This method is called by :meth:`rethinkmodel.manage.auto` function to
        prepare indexes in database.

        .. warning::

            This is a work in progress. At this time, you can only return a list of
            strings (name of properties to use as index)

        """
        return None


class Model(BaseModel):
    """Model is the parent class of all tables for RethinkDB

    The constructor accepts kwargs with attributes to set.

    For example, if the :code:User class is set like this:

    .. code::

        class User(Model):
            username: Type[str]

    You may construct the object with:

    .. code::

        user = User(username="John")
    """

    def __init__(self, **kwargs):
        """Construct the object with checks on types in annotations

        :code:kwargs is set to object attributes if they are declared in annotations
        """
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
        in __tablename__ attributes

        This method generates a pluralized name.

        - YYY  → YYYs
        - YYYx → XXXices
        - YYYy → YYYies

        e.g:

        - gallery  → galleries
        - matrix   → matrices
        - foo      → foos
        - analysis → analysis (no changes)

        :type: string

        """
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
            elif isinstance(val, list):
                data[name] = [
                    model.id if isinstance(model, Model) else model for model in val
                ]

        # set the id if it exists
        if self.id:
            data["id"] = self.id
        return data

    def save(self) -> "Model":
        """ Insert or update data if self.id is set. Return the save object (self)."""
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
            if res.get("errors") != 0:
                msg = f"An error occured on create in {self.tablename} entry: {res['first_error']}"
                raise errors.ReqlError(msg)
            self.on_modified()
        else:
            self.created_at = now
            data = self.todict()
            del data["id"]
            res = self.__r.table(self.tablename).insert(data).run(self.__conn)
            if res.get("errors") != 0:
                msg = f"An error occured on insert in {self.tablename} entry: {res['first_error']}"
                raise errors.ReqlError(msg)
            self.id = res.get("generated_keys")[0]
            self.on_created()
        return self

    @classmethod
    def get(cls, uid: str) -> Optional["Model"]:
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

    @classmethod
    def get_all(
        cls,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Union[Dict, str]] = None,
    ) -> List["Model"]:
        """ Get collection of results """

        select = {}
        if db.SOFT_DELETE:
            select["deleted_at"] = None

        rdb, conn = connect()
        query = cls.__prepare_query(rdb, limit, offset, order_by)
        results = query.filter(select).run(conn)
        conn.close()

        return [cls.__build(u) for u in results]

    def delete(self):
        """ Delete this object from DB """
        if db.SOFT_DELETE:
            self.__r.table(self.tablename).get(self.id).update(
                {"deleted_at": datetime.astimezone(datetime.now())}
            ).run(self.__conn)
        else:
            self.__r.table(self.tablename).get(self.id).delete().run(self.__conn)

        self.on_deleted()
        self.id = None

    @classmethod
    def delete_id(cls, idx: str):
        """ Delete the object that is identified by "id" """

        data = cls(id=idx)
        data.id = idx
        data.delete()

    @classmethod
    def __build(cls, result: dict) -> "Model":
        """ Build the object with nested object if there's Linked attributes """

        for name, kind in get_type_hints(cls).items():
            models = [m for m in get_args(kind) if issubclass(m, Model)]
            for model in models:
                if isinstance(result[name], list):
                    result[name] = [model.get(modelid) for modelid in result[name]]
                else:
                    result[name] = model.get(result[name])

        return cls(**result)

    @classmethod
    def filter(
        cls,
        select: Optional[Dict],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Union[Dict, str]] = None,
    ) -> Union[List["Model"]]:
        """ Select object in database with filters """

        # force not deleted object
        if db.SOFT_DELETE:
            select["deleted_at"] = None

        rdb, conn = connect()
        query = cls.__prepare_query(rdb, limit, offset, order_by)
        results = query.filter(select).run(conn)
        conn.close()

        return [cls.__build(u) for u in results]

    def join(
        self,
        *models: Type["Model"],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[Union[Dict, str]] = None,
    ) -> "Model":
        """ Join linked models to the current model, fetched by id """
        for model in models:
            if not issubclass(model, Model):
                continue

            # find the right attribute in "model" which is bounded to self class
            hints = get_type_hints(model)
            for name, hint in hints.items():
                args = get_args(hint)
                if self.__class__ in args:
                    fields = model.filter(
                        {name: self.id}, limit=limit, offset=offset, order_by=order_by
                    )
                    setattr(self, model.tablename, fields)

        return self

    @classmethod
    def truncate(cls):
        """ Truncate table, delete everything in the table """
        rdb, conn = connect()
        rdb.table(cls.tablename).delete().run(conn)
        conn.close()

    def __del__(self):
        self.__conn.close()

    def __dict__(self):
        return self.todict()

    def __repr__(self):
        return repr(self.todict())

    @classmethod
    def __prepare_query(
        cls,
        rdb: RethinkDB,
        limit: Optional[int],
        offset: Optional[int],
        order_by: Optional[Union[dict, str]],
    ) -> Any:

        query = rdb.table(cls.tablename)
        if order_by:
            query = query.order_by(order_by)

        if offset and offset > 0:
            query = query.skip(offset)

        if limit and limit > 0:
            query = query.limit(limit)

        return query

    # pylint: disable=useless-super-delegation
    def __getattribute__(self, name: str) -> Any:
        """Mainly done to avoid errors in IDE and editors when we want to access model properties"""
        return super().__getattribute__(name)
