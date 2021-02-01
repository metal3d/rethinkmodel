""" RethinkDB manager """
import os

from rethinkdb import RethinkDB

DB_NAME = os.environ.get("RM_DBNAME", "test")
PORT = int(os.environ.get("RM_PORT", 28015))
HOST = os.environ.get("RM_HOST", "127.0.0.1")
USER = os.environ.get("RM_USER", "admin")
PASSWORD = os.environ.get("RM_PASSWORD", "")
TIMEOUT = int(os.environ.get("RM_TIMEOUT", 20))
SSL = None
SOFT_DELETE = os.environ.get("RM_SOFT_DELETE", "false").lower() in (
    "true",
    "yes",
    "y",
    "1",
)


def connect():
    """ Return a RethinkDB object + connection """
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
