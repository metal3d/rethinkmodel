.. RethinkModel documentation master file, created by
   sphinx-quickstart on Wed Jan 27 14:38:31 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to RethinkModel's documentation!
========================================

What is this ?
--------------

RethinkModel aims to help you to describe your data as classes to be easilly created, updated and get from RethinkDB_.

Rethink:Model make uses of `typing support`_ annotations - Python annotations describe the `model` fields. That's easy, you only have to import the standard `typing` module, and use any of :code:`Optionnal`, :code:`Type`, :code:`List`, :code:`Union`... types.

.. note::

    Rethink:Model will not fully check your field types, it's designed to trust your IDE and your competences 💪.


It's simple as a pie
--------------------

.. code::

    from typing import Optional
    from rethinkdb.model import Model

    class Post(Model):
        author: User
        content: str
        tags: Optional[List[str]]

    class User(Model):
        login: str
        email: str

    user = User(login="John", email="me@foo.com").save()
    post = Post(author=user, content="This is the post").save()

Above example uses simple types, but you can do:

.. code::

    class Post(Model):
        author: Type[User]
        content: Type[str]
        tags: Optional[List[str]]

This way, your IDE will complain if you try to set something else than a :code:`User` in :code:`author`, :code:`None` in content...

The goals
---------

- Describe the models in the simplest possible way, but also in the most meaningful way
- Make use of powerful typing package from Python > 3.7
- Avoid type checking at runtime (What ?) but let your IDE punish you

Python is not a staticly typed langage. But Python developers want it (or not 😜) - So there are many Python tools that are designed to use typing package which is integrated with Python SDK: Pyright (use by PyLance), MyPy, PyType...

Your IDE can make type checking.

- Vim can use coc-pyright_
- VsCode can use PyLance_
- PyCharm knows how to manage typing
- etc...

So, let's use typing ! Rethink:Model is designed to use the typing package.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   project
   install
   manage
   basic-usage
   tutorials/index
   modules/index

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _RethinkDB: https://www.rethinkdb.com
.. _typing support: https://docs.python.org/3/library/typing.html
.. _coc-pyright: https://github.com/fannheyward/coc-pyright
.. _PyLance: https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance
