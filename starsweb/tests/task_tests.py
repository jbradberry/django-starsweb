from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.base import File

import os

from .. import models, tasks

PATH = os.path.dirname(__file__)


class ActivateGameTaskTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin',
                                             password='password')

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_activate_game(self):
        g = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
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

        result = tasks.activate_game.apply(args=[g.pk])

        g = models.Game.objects.get(pk=g.pk)

        self.assertNotEqual(g.options.file_contents, '')
        self.assertEqual(g.races.filter(player_number__isnull=False).count(), 2)
        self.assertIsNotNone(g.mapfile)
        self.assertEqual(g.turns.count(), 1)
        turn = g.turns.get()
        self.assertEqual(turn.year, 2400)
        self.assertEqual(turn.scores.count(), 0)
        self.assertIsNotNone(turn.hstfile)
        self.assertEqual(turn.raceturns.filter(mfile__isnull=False).count(), 2)
