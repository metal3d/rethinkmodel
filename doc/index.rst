.. RethinkModel documentation master file, created by
   sphinx-quickstart on Wed Jan 27 14:38:31 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to RethinkModel's documentation!
========================================

RethinkModel aims to help you to describe your data as classes to be easilly created, updated and get from RethinkDB.

The basic usage is to create a class with annotations to declare fields to save. For example:

There are 4 automatic fields comming from :code:`Model` class:

- :code:`id` is set by RethinkDB
- :code:`created_at` when you save an object without id (create)
- :code:`updated_at` when you save an object with a given id (update)
- :code:`deleted_at` is set to :code:`True` when you delete the object, and if you set :code:`rethinkmodel.db.SOFT_DELETE` to :code:`True`

.. code-block::

    from rethinkmodel import Model

    class User(Model):
        username: str
        password: str
        age: int

The types will be checked before to be saved in database. If the type is not respected, the :code:`rethinkmodel.exceptions.BadType` error is raised.

There are several types that helps to manage the tables and field.

- :code:`Checkers` defines some operation to check the attributes, for example :code:`rethinkmodel.checkers.NonNull` will check if the attribute is not, it raises `rethinkmodel.checkers.NonNullException` if the attribute is null
- :code:`Transformers` defines some rules to transform an attribute before save and when you get objects from database. For example :code:`rethinkmodel.transforms.Linked` is made to replace nested object to the object id.

For example:

.. code-block::

    class Project:
        name: (str, NonNull)
        owner: (User, Linked)


In the above example:

- :code:`name` couldn't be :code:`None`, you need to set a string
- :code:`owner` will be replaced by the :code:`User.id` field when you'll save the :code:`Project` in database. When you will get it back from database, the :code:`owner` attribute will contain the :code:`User` object.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/manage
   modules/init
   modules/model
   modules/checkers
   modules/transformations



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
