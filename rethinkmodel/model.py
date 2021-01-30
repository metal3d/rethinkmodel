""" Model definition """
from datetime import datetime

from . import actions, db
from .checkers import Checker
from .db import connect
from .exceptions import BadType, UnknownField
from .transforms import Linked, Transform


class Model:
    """ Model is the parent class of all tables for RethinkDB """

    created_at: datetime
    deleted_at: datetime
    updated_at: datetime

    def __init__(self, **kwargs):
        """ Construct the object with checks on types in annotations """
        # we must have ID
        self.id = None  # pylint: disable=invalid-name

        # keep connection
        self.__r, self.__conn = connect()
        self.created_at = None
        self.updated_at = None
        self.deleted_at = None

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

        # add the Model annotations
        for name, kind in getattr(Model, "__annotations__").items():
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
    def tablename(cls) -> str:
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
                if issubclass(kind, Checker):
                    kind.check(self, name)
        return True

    def todict(self, is_nested=False) -> dict:
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
                        objects.append(attr.todict(is_nested=True))
                    else:
                        objects.append(attr)
                data[name] = objects

            # or to be a Model
            elif hasattr(attribute, "todict"):
                data[name] = attribute.todict(is_nested=True)

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
        if is_nested:
            for attr in ("created", "updated", "deleted"):
                del data[attr + "_at"]
        return data

    def save(self) -> object:
        """ Insert or update data if self.id is set """

        # check if all attributes are ok
        self.__process_checkers()

        # prepare date and action type
        if self.id is None:
            self.created_at = datetime.astimezone(datetime.now())
            action_type = actions.ACTION_CREATE
        else:
            self.updated_at = datetime.astimezone(datetime.now())
            action_type = actions.ACTION_UPDATE

        # Find action annotaions
        todo = {}
        for field, kinds in self._annotations().items():
            actionlist = [kind for kind in kinds if issubclass(kind, actions.Action)]
            todo[field] = actionlist
        for field, act in todo.items():
            for action in act:
                action.do_action(self, field, action_type)

        data = self.todict()

        rdb, conn = self.__r, self.__conn
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
        self.delete_id(self.id, model=self)

    @classmethod
    def delete_id(cls, idx, model=None):
        """ Delete the object that is identified by "id" """
        assert idx is not None

        for field, annotations in cls._annotations().items():
            for annotation in annotations:
                if issubclass(annotation, actions.Action):
                    if model is None:
                        model = cls.get(idx)
                    annotation.do_action(model, field, actions.ACTION_DELETE)

        rdb, conn = connect()
        if db.SOFT_DELETE:
            rdb.table(cls.tablename).get(idx).update(
                {"deleted_at": datetime.astimezone(datetime.now())}
            ).run(conn)
        else:
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
            # we need to rebuild object from id or dict
            if isinstance(result[name], list):
                if Linked in kinds:
                    # build the objects for id list
                    result[name] = [
                        modelkind(id=data)
                        for data in result[name]
                        if not isinstance(data, Model)
                    ]
                else:
                    # build the objects from dict
                    result[name] = [
                        modelkind(**data)
                        for data in result[name]
                        if not isinstance(data, Model)
                    ]
            elif isinstance(result[name], dict):
                result[name] = modelkind(**result[name])

            # now, we need to manage the simple case of Linked
            # objects. In this case, result[name] is an "id"
            elif Linked in kinds and list not in kinds:
                # we need to find the linked element
                tofind = result[name]
                linked = modelkind.get(tofind)
                result[name] = linked

        return cls(**result)

    @classmethod
    def filter(cls, select: dict = None) -> dict:
        """ Select object in database with filters """

        # force not deleted object
        if db.SOFT_DELETE:
            select["deleted_at"] = None
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
