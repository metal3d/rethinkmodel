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

# Common methods

| Method          | Access          | Description                                                                                           |
| --------------- | --------------- | ----------------------------------------------------------------------------------------------------- |
| `get(id)`       | static method   | returns the object taken from database for the given ID, None if not found                            |
| `filter(id)`    | static method   | returns a list of found objects matching the `dict` selection                                         |
| `tablename`     | static property | produce the table name, can be override with `__tablename__` static property in your model definition |
| `todict()`      | method          | returns the `dict` representation, the format corresponds to what will be set in RethinkDB database   |
| `delete()`      | method          | delete the current object from database                                                               |
| `delete_id(id)` | static method   | method to call from you Model type to delete an object in database that is identified by the given id |

The complete documentation is in progress.

# What's next

- [ ] More checks on attributes to avoid multiple Model in attributes
- [ ] Take decision to save model in composite object (nested objects)
- [ ] Give possibility to propose "index" annotation
- [ ] Enhance filter method
- [ ] Cascade deletion (top/down)
