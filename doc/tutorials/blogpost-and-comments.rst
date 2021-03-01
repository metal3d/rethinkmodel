Example: blog post and comments
===============================

Let's create a simple blog posts databases with comments. You'll need to create:

- a `Post` model with title, tags and content fields
- a `Comment` wich is linked to Post

Why to not add a "comments" field inside `Post` Model ? Actually, you can. But there are 3 majors troubles that may happen:

- Create a "comment" means to "update" the post object, and so... you'll change the "updated_at" value
- Its possible (but not probable) that you can write a post at the same time as a comment, so one will overwrite the other
- And, if you've got a lot of comments for a post, the post object will be heavy

So, it's more efficient to link post inside the comments, and not comments inside the posts.

.. warning::

    In this case, cascading deletion should **not** be used. Deleting a blog post will not delete children comments. And if you set Cascade attribute to "post" on the comment object, you will **remove the post when a comment is deleted**. Keep in mind that the cascading deletion should **only** be ativate from the parent !

This is the model:

.. code-block::

    from typing import Optional, List
    from rethinkmodel import Model
    from rethtinkmodel.transforms import Linked
    from rethtinkmodel.checkers import NonNull

    class Post(Model)
        title: str
        content: Optional[str]
        tags: List[str]

    class Comment(Model)
        author: str
        content: str
        post: Type[Post] # make the link to Post

Now, let's create a blog post.

.. code-block::

    post = Post(
        title="My first post",
        content="This is the content",
        tags=["example", "article"],
    )
    post.save()

In database, you can find the article. The "post.id" field is set (uuid form), and you can use it to add a comments.

.. code-block::

    comment = Comment(
        author="Bob",
        content="Nice post dude",
        post=post
    )
    comment.save()

Inside RethinkDB database the comment object contains the :code:`post.id` value. But when you will get it, RethinkModel will fetches the **linked object**.
That means that you can get the title of the article by calling:

.. code-block::

    comment.post.title


Now, how to get comments from a post ? The easiest method is to use :code:`join()` method:

.. code-block::

    post = Post.get(post_id).join(Comment)
    post.comments # contains the Comment objects list


.. danger::

    The joined attribute is set from the joined tablename as described in your model. If you declared a propoerty with that name, **it will be overwritten** at fetch time. If you save the parent object, so you will write data. It is possible that Rethink:Model will prevent this later.

    .. code::

        # If you do this:
        class Post(Model):
            #...
            comments: Any

        # Then
        Post.get(post_id).Join(Comment)
        # the post.comments property is reset by the joined data.


You may also use :code:`filter` method to get comment list from a post ID:

.. code-block::

    comments = Comment.filter({
        "post" : post.id
    })


The :code:`comments` variable is a :code:`list` that contains comments for the post. The :code:`post` atribute of the entire comment list will be filled by the corresponding :code:`Post` object.

You can update them and use :code:`save` method as they have got "id". The :code:"updated_at" attribute will be automatically updated.
