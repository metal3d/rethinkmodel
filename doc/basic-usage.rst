Basic usage
===========

First step
----------

At first, you need to configure your database. Be sure that RethinkDB is launched and that you can access the service port.

By default, RethinkModel will check this environment variables:

- :code:`RM_DBNAME` to set the database to use, default is "test"
- :code:`RM_HOST` default to "127.0.0.1"
- :code:`RM_PORT` default to 28015
- :code:`RM_USER` default to "admin" (the RethinkDB default user)
- :code:`RM_PASSWORD` default to empty string (the RethinkDB default)
- :code:`RM_TIMEOUT` default to 10 (in seconds)
- :code:`RM_SOFT_DELETE` with is :code:`False` by default

If you want to configure this in python, you can use the :code:`rethinkmodel.config()` function.

Create models
--------------

The basic usage is to create a class with annotations to declare fields to save.

There are 4 automatic fields comming from :code:`Model` class:

- :code:`id` is set by RethinkDB
- :code:`created_at` when you save an object without id (create)
- :code:`updated_at` when you save an object with a given id (update)
- :code:`deleted_at` is set to deleted :code:`datatime` when you delete the object, and if you set :code:`rethinkmodel.db.SOFT_DELETE` to :code:`True`

.. code-block::

    # you must use typing
    from typing import Type
    from rethinkmodel import Model

    class User(Model):
        username: Type[str]
        password: Type[str]
        age: Type[int]


Rethink:Model automatically manages `One to One` and `One to Many` relations. The rule is to add an annotations that is Typed with a Model based class. The above example can help:


.. code-block::

    class Post(Model):
        title: Type[str]
        author: Type[User] # this will actually store the User.id
        tags: List[str]

    class Product(Model):
        name: Optional[str] # we can accept None
        categories: List[str]

    class Project(Model):
        name: Type[str]
        owner: Optional[User]

        # this will save a list of User IDs
        contributors: List[User]

See the :code:`Linked` documentation part have more details.
