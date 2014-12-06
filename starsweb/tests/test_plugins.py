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

    def test_get_owner_by_pk(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")

        owner = self.plugin.get_owner(self.game, {'owner_pk': r1.pk})
        self.assertEqual(owner, r1)

        try:
            owner = self.plugin.get_owner(self.game, {'owner_pk': r1.pk + 1})
        except Exception as e:
            self.fail(e)

        self.assertIsNone(owner)

    def test_get_owner_by_slug(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")

        owner = self.plugin.get_owner(self.game, {'owner_slug': r1.slug})
        self.assertEqual(owner, r1)

        try:
            owner = self.plugin.get_owner(self.game, {'owner_slug': "SSG"})
        except Exception as e:
            self.fail(e)

        self.assertIsNone(owner)

    def test_active_ambassador(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")
        a1 = r1.ambassadors.create(name="KonTiki", user=self.user, active=True)

        self.assertTrue(self.plugin._has_permission(self.user, r1))

    def test_inactive_ambassador(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")
        a1 = r1.ambassadors.create(name="Jeff", user=self.user, active=False)

        self.assertFalse(self.plugin._has_permission(self.user, r1))

    def test_user_not_on_race(self):
        r1 = self.game.races.create(name="Gestalti", plural_name="Gestalti",
                                    slug="gestalti")

        self.assertFalse(self.plugin._has_permission(self.user, r1))
