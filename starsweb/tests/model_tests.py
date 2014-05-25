from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.base import File

import os

from .. import models

PATH = os.path.dirname(__file__)


class StarsFileTestCase(TestCase):
    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_from_data(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)

        with open(os.path.join(PATH, 'files', 'ulf_war.xy')) as f:
            starsfile = models.StarsFile.from_data(f.read())

        self.assertEqual(starsfile.type, 'xy')

        self.assertEqual(models.StarsFile.objects.count(), 1)
        starsfile = models.StarsFile.objects.get()
        self.assertIsNotNone(starsfile.file)

    def test_from_file(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)

        with open(os.path.join(PATH, 'files', 'ulf_war.xy')) as f:
            xy_file = File(f)

            starsfile = models.StarsFile.from_file(xy_file)

        self.assertEqual(starsfile.type, 'xy')

        self.assertEqual(models.StarsFile.objects.count(), 1)
        starsfile = models.StarsFile.objects.get()
        self.assertIsNotNone(starsfile.file)

    def test_copy_from_starsfile_file(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)

        with open(os.path.join(PATH, 'files', 'ulf_war.xy')) as f:
            starsfile = models.StarsFile.from_data(f.read())

        starsfile2 = models.StarsFile.from_file(starsfile.file)

        self.assertEqual(models.StarsFile.objects.count(), 2)
        sfile1, sfile2 = models.StarsFile.objects.all()

        self.assertNotEqual(sfile1.file.path, sfile2.file.path)

    def test_parse(self):
        with open(os.path.join(PATH, 'files', 'ulf_war.xy')) as f:
            data = f.read()

        sfile = models.StarsFile.parse(data)
        self.assertEqual(sfile.type, 'xy')

        with self.assertRaises(ValueError):
            models.StarsFile.parse(data, 'r')


class GameTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')

    def test_create_new_game(self):
        self.assertFalse(models.Game.objects.exists())

        g = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
            description="This *game* is foobared.",
        )
        g.save()

        self.assertEqual(models.Game.objects.count(), 1)
        g = models.Game.objects.get()
        self.assertEqual(g.name, "Foobar")
        self.assertEqual(g.state, 'S')
        self.assertEqual(g.host.username, 'admin')
        self.assertEqual(g.description_html,
                         "<p>This <em>game</em> is foobared.</p>")

    def test_create_game_with_empty_description(self):
        self.assertFalse(models.Game.objects.exists())

        g = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
        )
        g.save()

        self.assertEqual(models.Game.objects.count(), 1)
        g = models.Game.objects.get()
        self.assertEqual(g.name, "Foobar")
        self.assertEqual(g.state, 'S')
        self.assertEqual(g.host.username, 'admin')
        self.assertEqual(g.description_html, "")


class RaceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.game = models.Game(name="",
                                slug="",
                                host=self.user,
                                description="")
        self.game.save()

    def test_create_new_race(self):
        race = models.Race(game=self.game,
                           name="Gestalti",
                           plural_name="Gestalti",
                           slug="gestalti")
        race.save()
        self.assertEqual(race.name, "Gestalti")
        self.assertEqual(race.plural_name, "Gestalti")
        self.assertEqual(race.slug, "gestalti")
        self.assertIsNone(race.player_number)

    def test_alter_existing_race(self):
        race = models.Race(game=self.game,
                           name="Gestalti",
                           plural_name="Gestalti",
                           slug="gestalti")
        race.save()
        self.assertEqual(race.name, "Gestalti")
        self.assertEqual(race.plural_name, "Gestalti")
        self.assertEqual(race.slug, "gestalti")
        self.assertIsNone(race.player_number)

        race.player_number = 0
        race.save()
        self.assertEqual(race.name, "Gestalti")
        self.assertEqual(race.plural_name, "Gestalti")
        self.assertEqual(race.slug, "gestalti")
        self.assertEqual(race.player_number, 0)
