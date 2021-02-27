""" Some test with linked models """
# pylint: disable=missing-class-docstring
from typing import List, Type
from unittest import TestCase

from rethinkmodel import config
from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from . import utils


class User(Model):
    name: Type[str]


class Gallery(Model):
    name: Type[str]
    contributors: List[User]


class Image(Model):
    name: Type[str]
    gallery: Type[Gallery]


utils.clean("tests_one_to_many")


class TestOneToMany(TestCase):
    def setUp(self) -> None:
        config(dbname="tests_one_to_many")
        manage(__name__)
        return super().setUp()

    def test_relations(self):
        """ Test to create a Galley with images """

        users = []
        for i in range(2):
            user = User(name=f"User{i}")
            user.save()
            users.append(user)

        gallery = Gallery(name="MyGallery", contributors=users)
        gallery.save()

        images = []
        for i in range(2):
            image = Image(name=f"imagename{i}", gallery=gallery)
            image.save()
            images.append(image)

        # we need to keep gallery id
        for image in images:
            self.assertIsNotNone(gallery.id)
            self.assertEqual(image.gallery.id, gallery.id)

        # fetch joined
        gallery = Gallery.get(gallery.id).join(Image)
        self.assertIsNotNone(gallery.images)
        self.assertGreater(len(gallery.images), 0)

        names = [n.name for n in images]
        for image in gallery.images:
            self.assertIsNotNone(image.name)
            self.assertIn(image.name, names)

        userids = [user.id for user in users]
        for user in gallery.contributors:
            self.assertTrue(isinstance(user, User))
            self.assertIn(user.id, userids)

        # fetch one image that is linked to specific gallery
        filtered_images = Image.filter({"gallery": gallery.id})
        self.assertGreater(len(filtered_images), 0)
        for image in filtered_images:
            self.assertEqual(image.gallery.id, gallery.id)
