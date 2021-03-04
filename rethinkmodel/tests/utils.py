"""Generic test utils."""

from rethinkdb import errors
from rethinkmodel import config, db
from rethinkmodel.db import connect


def clean(dbname: str):
    """Test utils, clean database to recreate it."""
    db.DB_NAME = dbname
    config(dbname=dbname)
    rdb, conn = connect()
    try:
        rdb.db_drop(dbname).run(conn)
    except errors.ReqlOpFailedError:
        pass

    rdb.db_create(dbname).run(conn)
    conn.close()
