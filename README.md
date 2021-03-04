# Rethink:Model

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/e73c388432a441b8aae9ba2e7ef502e4)](https://app.codacy.com/gh/metal3d/rethinkmodel?utm_source=github.com&utm_medium=referral&utm_content=metal3d/rethinkmodel&utm_campaign=Badge_Grade_Settings)
[![Build Status](https://www.travis-ci.org/metal3d/rethinkmodel.svg?branch=master)](https://www.travis-ci.org/metal3d/rethinkmodel)
[![documentation](https://badgen.net/badge/doc/official/green)](https://metal3d.github.io/rethinkmodel)

Simple and easy to use ORM for [RethinkDB](https://www.rethinkdb.com). Use Python `typing` package and annotations to describe data representation.

RethinkModel aims to help you to describe your data as classes to be
easilly created, updated and get from
[RethinkDB](https://www.rethinkdb.com).

Rethink:Model make uses of [typing support](https://docs.python.org/3/library/typing.html) annotations - Python annotations describe the model fields. That's easy, you only have to import the standard `typing` module, and use any of `Optionnal`, `Type`, `List`, `Union`... types.

## It's simple as a pie

```python
from typing import Optional, List
from rethinkdb.model import Model

class Post(Model):
    author: User  # One to One relation to User
    content: str
    tags: Optional[List[str]] # use typing, tags can be None

class User(Model):
    login: str
    email: str

# save
user = User(login="John", email="me@foo.com").save()
post = Post(author=user, content="This is the post").save()

# get user
user = User.get(user.id)

# get Post
post = Post.get(post.id)
# post.author is an User, but in DB it's the ID

# get post from User ?
user = User.get(user.id).join(Project)
# user.projects is now filled
```

There are **other methods** like `join()`, `get_all()` and so on. Please check documentation. 

## The goals

- Describe the models in the simplest possible way, but also in the most meaningful way
- Make use of powerful typing package from Python > 3.7
- Avoid type checking at runtime (What ?) but let your IDE punish you

Python is not a staticly typed langage. But Python developers want it
(or not 😜) - So there are many Python tools that are designed to use
typing package which is integrated with Python SDK: Pyright (use by
PyLance), MyPy, PyType...

Your IDE can make type checking.

- Vim can use [coc-pyright](https://github.com/fannheyward/coc-pyright)
- VsCode can use [PyLance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
- PyCharm knows how to manage typing
- etc...

So, let's use typing ! Rethink:Model is designed to use the typing package.
