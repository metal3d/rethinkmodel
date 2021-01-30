""" Actions are annotations to declare special actions """
# pylint: disable=too-few-public-methods
from abc import abstractmethod
from collections.abc import Iterable

from .transforms import Linked

ACTION_CREATE = 0
ACTION_UPDATE = 1
ACTION_DELETE = 2


class Action:
    """ Action must have a `do_action` method """

    @classmethod
    @abstractmethod
    def do_action(cls, model: object, field: str, action: int):
        """ Do some actions on the model """


class Cascade(Action):
    """ Delete Linked objects """

    @classmethod
    def do_action(cls, model: object, field: str, action: int):
        """ If the field is Linked to children, so delete children """
        if action != ACTION_DELETE:
            return

        annotations = model.__annotations__[field]
        if not isinstance(annotations, tuple):
            annotations = (annotations,)

        if Linked not in annotations:
            return

        # OK, now we knows that the Linked field should be deleted
        fields = getattr(model, field)

        # be sure to have the field
        if not isinstance(fields, Iterable):
            fields = (fields,)

        for obj in fields:
            obj = obj.__class__(**obj.todict())
            obj.delete()
