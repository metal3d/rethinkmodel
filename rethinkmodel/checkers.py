""" Checkers annotations makes some checks before to save a Model object in database.

All checker should raise Exception when the check fails.

E.g.:

.. code-block::

    class User:
        # the field value must be unique in database
        username: (str, Unique)
        # the field must be not None
        password: (str, NonNull)

Checkers can be cumulated.
"""
# pylint: disable=too-few-public-methods
from abc import abstractmethod

from .exceptions import NonNullException, UniqueException


class Checker:
    """Checkers make some checks on attribute,
    all derived class must implement the :code:`check(cls, model, field)` method.
    `model` is the object where to find the `field`
    """

    @classmethod
    @abstractmethod
    def check(cls, model, field):
        """Apply the checkpoint, each checker must
        raise an exception if it fails.
        """


class Unique(Checker):
    """ Check unicity of the field """

    @classmethod
    def check(cls, model, field):
        """Fetch the field in the model in db, and
        raise :code:`UniqueException` if the value already exists"""
        value = getattr(model, field)
        res = model.filter({field: value})
        if res is not None:
            raise UniqueException(f"unique {field} value already exists")


class NonNull(Checker):
    """ Check if the attribute is None """

    @classmethod
    def check(cls, model, field):
        """ Check if field is None or raise :code:`NonNullException` """
        if getattr(model, field) is None:
            raise NonNullException(f"{field} value cannot be None")
