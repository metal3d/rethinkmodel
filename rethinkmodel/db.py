""" 
RethinkDB connection manager
============================

It only contains the :code:`connect()` function. It's preferable to use
the :meth:`rethinkmodel.config()` function to set up connection informations
before to call :code:`connec()` function, or use environment variables.

- RM_DBNAME
- RM_PORT
- RM_HOST
- RM_USER
- RM_PASSWORD
- RM_TIMEOUT

"""
import os
from typing import Any, Tuple

from rethinkdb import RethinkDB

DB_NAME = os.environ.get("RM_DBNAME", "test")
PORT = int(os.environ.get("RM_PORT", 28015))
HOST = os.environ.get("RM_HOST", "127.0.0.1")
USER = os.environ.get("RM_USER", "admin")
PASSWORD = os.environ.get("RM_PASSWORD", "")
TIMEOUT = int(os.environ.get("RM_TIMEOUT", 20))
SSL: Any = None
SOFT_DELETE = os.environ.get("RM_SOFT_DELETE", "false").lower() in (
    "true",
    "yes",
    "y",
    "1",
)


def connect() -> Tuple[RethinkDB, Any]:
    """Return a RethinkDB object + connection

    You will usually not need to call this function. Rethink:Model use this
    function to internally open and close database connection.
    """
    rdb = RethinkDB()
    connection = rdb.connect(
        host=HOST,
        port=PORT,
        db=DB_NAME,
        user=USER,
        password=PASSWORD,
        timeout=TIMEOUT,
        ssl=SSL,
    )
    return rdb, connection
