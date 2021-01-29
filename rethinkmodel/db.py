""" RethinkDB manager """
import os

from rethinkdb import RethinkDB

DB_NAME = os.environ.get("RDB_MODEL_DBNAME", "test")
PORT = int(os.environ.get("RDB_PORT", 28015))
HOST = os.environ.get("RDB_HOST", "127.0.0.1")
USER = os.environ.get("RDB_USER", "admin")
PASSWORD = os.environ.get("RDB_PASSWORD", "")
TIMEOUT = int(os.environ.get("RDB_TIMEOUT", 20))
SSL = None
SOFT_DELETE = False


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
