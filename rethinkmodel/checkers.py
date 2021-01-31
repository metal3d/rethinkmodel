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

from .exceptions import BadType, NonNullException, UniqueException


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

    @classmethod
    @property
    def type(cls):
        """ Gives the representation type if needed """
        return None


class List(Checker):  # pylint: disable=abstract-method
    """ A list check """

    @classmethod
    def check(cls, model, field):
        """Check if the element is a list,
        either raise :code:`BadType` exception."""
        element = getattr(model, field)
        if not isinstance(element, list):
            raise BadType(f"The {field} attribute should be a list, not {type(field)}")

    @classmethod
    @property
    def type(cls):
        return list


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


class StringList(List):
    """ Ensure it's a string list """

    @classmethod
    def check(cls, model, field):
        """Check if the field is a list of strings
        or raise a :code:`BadType` exception"""
        super().check(model, field)
        elements = getattr(model, field)

        for element in elements:
            if not isinstance(element, str):
                raise BadType(
                    f"{field} should be a list of strings, it contains a {type(element)}"
                )


class FloatList(List):
    """ Ensure it's a float list """

    @classmethod
    def check(cls, model, field):
        """Check if field is a list of float or
        raise a :code:`BadType` exception"""
        super().check(model, field)
        elements = getattr(model, field)

        for element in elements:
            if not isinstance(element, float):
                raise BadType(
                    f"{field} should be a list of strings, it contains a {type(element)}"
                )


class IntList(List):
    """ Ensure it's a integer list """

    @classmethod
    def check(cls, model, field):
        """Check if field is a list of integer or
        raise a :code:`BadType` exception"""
        elements = getattr(model, field)
        if not isinstance(elements, list):
            raise BadType(f"{field} should be a list, not {type(elements)}")

        for element in elements:
            if not isinstance(element, int):
                raise BadType(
                    f"{field} should be a list of strings, it contains a {type(element)}"
                )
