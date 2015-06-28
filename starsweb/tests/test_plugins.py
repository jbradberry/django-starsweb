from django.contrib.auth.models import User
from django.test import TestCase

from .. import models, plugins


class TurnGenerationTestCase(TestCase):
    def setUp(self):
        self.plugin = plugins.TurnGeneration()
        self.user = User.objects.create_user(username='test',
                                             password='password')

        self.game = models.Game(
            name="Foobar",
            slug="foobar",
            host=self.user,
            description="This *game* is foobared.",
        )
        self.game.save()
        models.GameOptions.objects.create(game=self.game)

    def test_active_ambassador(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")
        a1 = r1.ambassadors.create(name="KonTiki", user=self.user, active=True)

        perms = (
            'turngeneration.add_pause',
            'turngeneration.change_pause',
            'turngeneration.delete_pause',
            'turngeneration.add_ready',
            'turngeneration.change_ready',
            'turngeneration.delete_ready',
        )

        for perm in perms:
            self.assertTrue(self.user.has_perm(perm, r1))

    def test_inactive_ambassador(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")
        a1 = r1.ambassadors.create(name="Jeff", user=self.user, active=False)

        perms = (
            'turngeneration.add_pause',
            'turngeneration.change_pause',
            'turngeneration.delete_pause',
            'turngeneration.add_ready',
            'turngeneration.change_ready',
            'turngeneration.delete_ready',
        )

        for perm in perms:
            self.assertFalse(self.user.has_perm(perm, r1))

    def test_user_not_on_race(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")

        perms = (
            'turngeneration.add_pause',
            'turngeneration.change_pause',
            'turngeneration.delete_pause',
            'turngeneration.add_ready',
            'turngeneration.change_ready',
            'turngeneration.delete_ready',
        )

        for perm in perms:
            self.assertFalse(self.user.has_perm(perm, r1))
