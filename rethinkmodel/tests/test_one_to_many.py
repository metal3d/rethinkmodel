""" Some test with linked models """
from typing import Type
from unittest import TestCase

from rethinkmodel import config
from rethinkmodel.manage import manage
from rethinkmodel.model import Model

from . import utils


class Gallery(Model):
    name: Type[str]


class Image(Model):
    name: Type[str]
    gallery: Type[Gallery]


utils.clean("tests_one_to_many")


class TestOneToMany(TestCase):
    def setUp(self) -> None:
        config(dbname="tests_one_to_many")
        manage(__name__)
        return super().setUp()

    def test_save(self):
        """ Test to create a Galley with images """

        gallery = Gallery(name="MyGallery")
        gallery.save()

        images = []
        for i in range(2):
            image = Image(name=f"imagename{i}", gallery=gallery)
            image.save()
            images.append(image)

        # we need to keep gallery id
        for im in images:
            self.assertIsNotNone(gallery.id)
            self.assertEqual(im.gallery.id, gallery.id)

        # fetch one image
        im = Image.filter({"gallery": gallery.id})
        self.assertGreater(len(im), 0)
        self.assertEqual(im[0].gallery, gallery.id)

        # fetch joined
        gallery = Gallery.get(gallery.id).join(Image)
        self.assertIsNotNone(gallery.images)
        self.assertGreater(len(gallery.images), 0)

        names = [n.name for n in images]
        for im in gallery.images:
            self.assertIsNotNone(im.name)
            self.assertIn(im.name, names)
