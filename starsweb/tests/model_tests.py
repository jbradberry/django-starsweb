from django.contrib.auth.models import User
from django.test import TestCase

from .. import models


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
