""" Transforms are annotations to modify attributes before to save or get/filter returns """
# pylint: disable=too-few-public-methods
from abc import abstractmethod


class Transform:
    """ Apply transformation on atrributes """

    @classmethod
    @abstractmethod
    def tranform(cls, model, field):
        """ Apply the transformation """


class Linked(Transform):
    """ Link object with id instead of setting the entire object """

    @classmethod
    @abstractmethod
    def transform(cls, model, field):
        """ Set the field to the linked object id """
        element = getattr(model, field)
        return getattr(element, "id")
