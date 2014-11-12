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
        self.user = User.objects.create_user(username='admin',
                                             password='password')

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_create_new_game(self):
        self.assertFalse(models.Game.objects.exists())

        g = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
            description="This *game* is foobared.",
        )
        g.save()
        models.GameOptions.objects.create(game=g)

        self.assertEqual(models.Game.objects.count(), 1)
        g = models.Game.objects.get()
        self.assertEqual(g.name, "Foobar")
        self.assertEqual(g.state, 'S')
        self.assertEqual(g.host.username, 'admin')
        self.assertEqual(g.description_html,
                         "<p>This <em>game</em> is foobared.</p>\n")
        self.assertIsNotNone(g.options)

    def test_create_game_with_empty_description(self):
        self.assertFalse(models.Game.objects.exists())

        g = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
        )
        g.save()
        models.GameOptions.objects.create(game=g)

        self.assertEqual(models.Game.objects.count(), 1)
        g = models.Game.objects.get()
        self.assertEqual(g.name, "Foobar")
        self.assertEqual(g.state, 'S')
        self.assertEqual(g.host.username, 'admin')
        self.assertEqual(g.description_html, "")

    def test_generate(self):
        g = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
            state='S',
            description="This *game* is foobared.",
        )
        g.save()
        opts = models.GameOptions.objects.create(game=g)

        r1 = g.races.create(name="Gestalti", plural_name="Gestalti",
                            slug="gestalti")
        r2 = g.races.create(name="SSG", plural_name="SSG", slug="ssg")

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            r1.racefile = models.StarsFile.from_file(File(f))
            r1.save()

        with open(os.path.join(PATH, 'files', 'ssg.r1')) as f:
            r2.racefile = models.StarsFile.from_file(File(f))
            r2.save()

        # Activate the game.
        try:
            g.generate()
        except Exception as e:
            self.fail(e)

        g = models.Game.objects.get(pk=g.pk)

        self.assertEqual(g.state, 'A')
        self.assertNotEqual(g.options.file_contents, '')
        self.assertEqual(g.races.filter(player_number__isnull=False).count(), 2)
        self.assertIsNotNone(g.mapfile)
        self.assertEqual(g.turns.count(), 1)
        turn = g.turns.get()
        self.assertEqual(turn.year, 2400)
        self.assertEqual(turn.scores.count(), 0)
        self.assertIsNotNone(turn.hstfile)
        self.assertEqual(turn.raceturns.filter(mfile__isnull=False).count(), 2)

        # Generate a turn for already active game.
        try:
            g.generate()
        except Exception as e:
            self.fail(e)

        g = models.Game.objects.get(pk=g.pk)

        self.assertEqual(g.state, 'A')
        self.assertNotEqual(g.options.file_contents, '')
        self.assertEqual(g.races.filter(player_number__isnull=False).count(), 2)
        self.assertIsNotNone(g.mapfile)
        self.assertEqual(g.turns.count(), 2)
        self.assertTrue(g.turns.filter(year=2401).exists())
        turn = g.turns.filter(year=2401).get()
        self.assertEqual(turn.scores.count(), 2 * 9)
        self.assertIsNotNone(turn.hstfile)
        self.assertEqual(turn.raceturns.filter(mfile__isnull=False).count(), 2)


class GameOptionsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin',
                                             password='password')
        self.game = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
            description="This *game* is foobared.",
        )
        self.game.save()

    def test_render(self):
        options = models.GameOptions.objects.create(game=self.game)

        self.game.races.create(name="Foo", plural_name="Foo", player_number=0)

        winpath = r"C:\\stars\\game\\"
        output = options.render(winpath)

        output_lines = output.split('\n')

        self.assertEqual(output_lines[0], "Foobar")
        self.assertEqual(output_lines[1], "1 1 1")
        self.assertEqual(output_lines[2], "0 0 0 0 0 1 0")
        self.assertEqual(output_lines[3], "1") # number of races
        self.assertEqual(output_lines[4], r"C:\\stars\\game\\race.r1")
        self.assertIn("0\n"*7, output)
        self.assertEqual(output_lines[12], "1 50")
        self.assertEqual(output_lines[13], r"C:\\stars\\game\\foobar.xy")

    def test_ai_render(self):
        options = models.GameOptions.objects.create(game=self.game,
                                                    ai_players='0,4')

        self.game.races.create(name="Foo", plural_name="Foo", player_number=0)

        options = models.GameOptions.objects.get()

        winpath = r"C:\\stars\\game\\"
        output = options.render(winpath)

        output_lines = output.split('\n')

        self.assertEqual(output_lines[0], "Foobar")
        self.assertEqual(output_lines[1], "1 1 1")
        self.assertEqual(output_lines[2], "0 0 0 0 0 1 0")
        self.assertEqual(output_lines[3], "2") # number of races
        self.assertEqual(output_lines[4], r"C:\\stars\\game\\race.r1")
        self.assertEqual(output_lines[5], "# 0 4")
        self.assertIn("0\n"*7, output)
        self.assertEqual(output_lines[13], "1 50")
        self.assertEqual(output_lines[14], r"C:\\stars\\game\\foobar.xy")


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
