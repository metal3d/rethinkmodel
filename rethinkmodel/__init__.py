""" RethinkDB Model base functions.

Proposes the :code:`config` function that must be called **before** any work on RethinkDB.
If you don't call the :code:`config` function, rethink:model will use default values to
connect "test" ddatabase on localhost:28015.

The *config* function will keep connection information inside the
*rethinkmodel.db* package.

.. note::

    this will probably change in future releases to allow usage of multiple
    databases connections.
"""

from . import db

__version__ = "0.1.0"


def config(  # pylint: disable=too-many-arguments
    user: str = db.USER,
    password: str = db.PASSWORD,
    host: str = db.HOST,
    port: int = db.PORT,
    dbname: str = db.DB_NAME,
    timeout: int = db.TIMEOUT,
    ssl: dict = db.SSL,
    soft_delete=db.SOFT_DELETE,
):
    """Configure database connection

    This **must** be called **before** any Model method call !
    """
    db.USER = user
    db.PASSWORD = password
    db.HOST = host
    db.PORT = port
    db.DB_NAME = dbname
    db.TIMEOUT = timeout
    db.SSL = ssl
    db.SOFT_DELETE = soft_delete
