# RethinkModel

This package is inspired of what we can do with SQLAlquemy by using a "Model pattern" to describe tables and fields for [RethinkDB](https://www.rethinkdb.com). The main differences are:

- because RethinkDB is document based, we don't use SQL but `dict` representation
- the `Model` class which is the ancestor class of tables uses "annotations" instead of static properties
- for nested objects, you have the possibility to "link" or "hold" the objects

The choice of annotation was made for the ease of writing, but it is also done to avoid errors. Annotations can only contain "types" instead of entity representation object.

An example:

```python
class User(Model):
    username: (str, Unique)
    email: (str, Unique)
    password: str

class Project(Model)
    name: str
    owner: (User, Linked) # Linked => only saves the "id"

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

There are others methods like:

- `get(id)` (static method) returns the object identified by the given id
- `filter(select)` (static method) returns a list of found data matching the "`select`" dict
- `tablename` (static property) returns the created or overridden table name
- `todict()`(method) returns the constructed dict representation
- `delete(id=None)` (static method) delete an entry - if called from class, the id must be given, if called from object, the id is taken from the current object itself (**there is no cascading deletion at this time**)
