""" Checkers are used as annotations to make some checks on attributes """
# pylint: disable=too-few-public-methods
from abc import abstractmethod

from .exceptions import NonNullException, UniqueException


class Checker:
    """ Checkers make some checks on attribute """

    @classmethod
    @abstractmethod
    def check(cls, model, field):
        """ Apply the checkpoint """


class Unique(Checker):
    """ Check unicity of the field """

    @classmethod
    def check(cls, model, field):
        """Fetch the field in the model in db, and
        raise UniqueException if the value already exists"""
        value = getattr(model, field)
        res = model.filter({field: value})
        if res is not None:
            raise UniqueException(f"unique {field} value already exists")


class NonNull(Checker):
    """ Check if the attribute is None """

    @classmethod
    def check(cls, model, field):
        """ Check if field is None or raise NonNullException """
        if getattr(model, field) is None:
            raise NonNullException(f"{field} value cannot be None")
