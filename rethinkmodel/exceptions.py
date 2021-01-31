""" Refer all possible exception in the package """


class NonNullException(Exception):
    """ Error for attribute set to None """


class UnknownField(Exception):
    """ Error if the field is not annotated """


class BadType(Exception):
    """ Error if the type is not in annation """


class UniqueException(Exception):
    """ Error if the field already exists with this value in db """


class TooManyModels(Exception):
    """ Error if an annotation as more than one Model subclass """
