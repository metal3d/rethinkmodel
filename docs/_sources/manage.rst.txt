Managing database and tables creation
=====================================

You will need to create your database and tables before to use the module. Rethink:Model propose :mod:`rethinkmodel.manage` module wich includes some tools to make this.

.. note::

    Because the :code:`manage` module will import your package, we **strongly** recommend to declare your models in a separated module where there is no code to execute.

Python way
----------

It's possible to use create database and tables when you start your project (e.g. with Flask). In your main module (the script you launch to start your project), import the module where you defined your models. Then, use the :code:`connect()`, :code:`checkdb()` and :code:`auto` functions:

.. code::

    from rethinkmodel
    from rethinkmodel.manage as manage 

    import mydata # this is your package or module

    rethinkmodel.config(dbname="mydatabase")
    manage.check_db() # creates the database if needed
    manage.manage(mydata) # will introspect your module

Above code will find the entire list of models that you defined and create tables. If you defined :code:`get_indexes()` methods, the indices are created in RethinkDB.

It's also possible to use package name instead of importing it.

.. code::

    from rethinkmodel
    from rethinkmodel.manage as manage 

    rethinkmodel.config(dbname="mydatabase")
    manage.check_db() # creates the database if needed

    # here, the module is imported by the manage method
    manage.manage("mydata")



Shell way
---------

Another possibility is to call the :mod:`rethinkmodel.manage` from command line giving the path to your data modules.

In this case, you'll need to use evironment variable to define where is your database, user name, passowrd, port... see :mod:`rethinkmodel.db` documentation to know the list of variables

.. code:: shell

    export RM_DBNAME="mydatabase"
    python -m rethinkmodel.manage path/to/data

