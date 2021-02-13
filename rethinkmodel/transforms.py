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
    """ Link the attribute with "one to many" relation.

    The attribute will keep the ID of the found Model in attribute.

    .. code-block::

        class User(Model):
            username: (str, NonNull)

        class Post(Model):
            title: str
            content: str
            user: (User, Linked)

    Here, the user is linked to the post.

    There are two behaviors:

    - if you get the Post object from database, the "user" field will contain \
            the corresponding user
    - if you get the User object from database, you may use :code:`join()` \
            method to link the User. In this case, the User object will have \
            a "virtual" field named "projects" (table name) with is a list \
            of Users

    .. code-block::

        project = Project.get(id)
        print(project.user.username) # displays the username

        user = User.get(id).join(Project)
        print(user.projects[0].name) # displays the project name

    .. note::

        Linked objects are real objects, so you can modify the child object
        and save it as any other Model.


    .. warning::

        Not recommanded: Linked can be a list, in this specific case the
        attribute will contain the list of children IDs.

        This can be useful if you have specific cases with not too much of
        data to inject in one field as list. But, keep in mind that the better
        implementation is to set a "parent" field inside the child Model, and
        not to keep "children" inside the parent.



    """

    @classmethod
    @abstractmethod
    def transform(cls, model, field):
        """ Set the field to the linked object id """
        element = getattr(model, field)

        # it coud be a list
        if isinstance(element, list):
            return [e.id for e in element]

        # default is to return the element id
        return getattr(element, "id")
