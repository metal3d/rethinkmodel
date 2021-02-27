# Rethink:Model

[![Build Status](https://www.travis-ci.org/metal3d/rethinkmodel.svg?branch=master)](https://www.travis-ci.org/metal3d/rethinkmodel)
[![codecov](https://codecov.io/gh/metal3d/rethinkmodel/branch/master/graph/badge.svg?token=JCBPHFQSHF)](https://codecov.io/gh/metal3d/rethinkmodel)

Use Python `typing` package and annotation to describe data for RethinkDB.

This package is inspired of what we can do with SQLAlquemy by using a "Model pattern" to describe tables and fields for [RethinkDB](https://www.rethinkdb.com). The main differences are:

- because RethinkDB is document based, we don't use SQL but `dict` representation
- the `Model` class which is the ancestor class of tables uses "annotations" instead of static properties

The choice of annotation was made for the ease of writing, but it is also done to avoid errors. Annotations can only contain "types" instead of entity representation object.

An example:

```python

from typing import Optional, Type
from rethinkmodel.model import Model

class User(Model):
    username: Type[str]
    email: Optional[str]
    password: Type[str]

class Project(Model)
    name: Type[str]
    owner: Type[User]

### Save objects in DB
user = User(username="foo", email="me@domain", password="secret")
user.save()
# the user.id field is now set by database, user is still a User object
print(user.id) # display the id

# linked annotation:
project = Project(name="my website", owner=user)
project.save()
# because Project.owner is tagged as "Linked",
# the project.owner field is converted in database to store the "ID"
# If the field had not been tagged as "Linked", then the object of
# type "User" would have been written entirely in the "owner" f
# field (as a document).

#### GET objects from DB

# you may get the user like this
dbuser = User.get(user.id) # returns the user from database

# nested object are reconstructed
dbproj = Project.get(project.id)

# now, dbproj.owner is a User object, even if in db it's an ID
```

