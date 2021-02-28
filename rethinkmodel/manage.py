"""
Automatic database initialisation tools
=======================================

This module proposes some functions to automatically create database and
tables by introspecting modules. It can be used in Python, or from command line (in progress).

The way to go is th create a python script, named "manage.py" for example, that will do
the job. For example:

.. code-block::

    import rethinkmodel
    import manage from rethinkmodel.manage

    import myproject.dataModule # this is your module

    # you should configure your RethinkDB connection here
    rethinkmodel.config(...)

    # Check if the configured database exists
    manage.check_db()

    # this will introspect module to find
    # each "Model" object and create tables.
    # It will also create database
    manage(myproject.dataModule)



"""
import glob
import importlib
import importlib.util
import inspect
import logging
import os.path
import sys
from typing import Any, Type

from rethinkdb import RethinkDB

from rethinkmodel import db
from rethinkmodel.model import Model

LOG = logging.getLogger("rethinkmodel")
LOG.setLevel(logging.INFO)


def check_db():
    """ Check if DB_NAME exists, or create it """
    rdb = RethinkDB()
    conn = rdb.connect(
        host=db.HOST,
        port=db.PORT,
        user=db.USER,
        password=db.PASSWORD,
        ssl=db.SSL,
        timeout=db.TIMEOUT,
    )

    dbs = rdb.db_list().run(conn)
    if db.DB_NAME not in dbs:
        LOG.info("create database %s", db.DB_NAME)
        rdb.db_create(db.DB_NAME).run(conn)

    conn.close()


def auto(member: Type[Model]):
    """ automatic database and table creation for the given type (Model child)"""

    if not issubclass(member, Model) or member is Model:
        return

    rdb = RethinkDB()
    conn = rdb.connect(
        host=db.HOST,
        port=db.PORT,
        db=db.DB_NAME,
        user=db.USER,
        password=db.PASSWORD,
        ssl=db.SSL,
        timeout=db.TIMEOUT,
    )

    tables = rdb.table_list().run(conn)
    if member.tablename not in tables:
        LOG.info("create table %s", member.tablename)
        rdb.table_create(member.tablename).run(conn)
        indexes = member.get_indexes()
        if indexes:
            # TODO: at this time, it's only working with simple index
            for index in indexes:
                rdb.table(member.tablename).index_create(index).run(conn)
                rdb.table(member.tablename).index_wait(index).run(conn)

    conn.close()


def manage(mod: Any):
    """Get all classes from given module and
    call "auto()" function to create table. This function accept
    a module, or the module name as string."""
    imported = mod
    if isinstance(mod, str):
        imported = importlib.import_module(mod)
    members = inspect.getmembers(imported)

    for _, obj in members:
        if inspect.isclass(obj):
            auto(obj)


def introspect(modpath: str):
    """ Introspect module inside a given path """
    name = os.path.basename(modpath)
    name = name.replace(".py", "")

    try:
        spec = importlib.util.spec_from_file_location(name, modpath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.load_module(mod.__name__)
    except ImportError:
        return

    manage(mod)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        for m in glob.glob("%s/**/*.py" % p, recursive=True):
            introspect(m)
