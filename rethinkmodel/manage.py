""" Automatic database initialisation tool 

This module proposes some functions to automatically create database and
tables by introspecting modules.

This can be also called by command line:

    python -m rethinkdb.manage <path>

With <path> is the directory to parse. You may give the path of your project.

"""
import glob
import importlib
import inspect
import logging
import os.path
import sys

from rethinkdb import RethinkDB

from . import Model, db

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


def auto(member):
    """ automatic database and table creation """

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

    conn.close()


def manage(mod):
    """Get all classes from given module and
    call "auto()" function to create table"""
    if isinstance(mod, str):
        mod = __import__(mod)
    members = inspect.getmembers(mod)
    for _, obj in members:
        if inspect.isclass(obj):
            auto(obj)


def introspect(modpath):
    """ Introspect module by a given path """
    name = os.path.basename(modpath)
    name = name.replace(".py", "")

    try:
        spec = importlib.util.spec_from_file_location(name, modpath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except ImportError:
        return

    manage(mod)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        for m in glob.glob("%s/**/*.py" % p, recursive=True):
            introspect(m)
