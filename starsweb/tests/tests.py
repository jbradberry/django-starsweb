from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from django.conf import settings

from .. import models


class GameModelTestCase(TestCase):
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


class GameCreateViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

    def test_create_new_game(self):
        self.user.is_superuser = True
        self.user.save()

        self.assertFalse(models.Game.objects.exists())

        response = self.client.get(reverse('create_game'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('create_game'),
            {'name': "Foobar",
             'slug': "foobar",
             'description': "This *game* is foobared.",
             'markup_type': "markdown",
             'published': True,},
            follow=True
        )
        self.assertEqual(models.Game.objects.count(), 1)
        g = models.Game.objects.get()
        self.assertEqual(g.name, "Foobar")
        self.assertEqual(g.state, 'S')
        self.assertEqual(g.host.username, 'admin')
        self.assertContains(response, "This <em>game</em> is foobared.")

    def test_create_game_with_empty_description(self):
        self.user.is_superuser = True
        self.user.save()

        self.assertFalse(models.Game.objects.exists())

        response = self.client.get(reverse('create_game'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('create_game'),
            {'name': "Foobar",
             'slug': "foobar",
             'description': "",
             'markup_type': "markdown",
             'published': True,},
            follow=True
        )
        self.assertEqual(models.Game.objects.count(), 1)
        g = models.Game.objects.get()
        self.assertEqual(g.name, "Foobar")
        self.assertEqual(g.state, 'S')
        self.assertEqual(g.host.username, 'admin')
        self.assertEqual(g.description_html, "")

    def test_attempt_create_without_permissions(self):
        self.assertFalse(models.Game.objects.exists())

        create_url = reverse('create_game')
        response = self.client.get(create_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   create_url))

        response = self.client.post(
            create_url,
            {'name': "Foobar",
             'slug': "foobar",
             'description': "This *game* is foobared.",
             'markup_type': "markdown",
             'published': True,},
        )
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   create_url))
        self.assertFalse(models.Game.objects.exists())

    def test_attempt_create_with_anonymous_user(self):
        self.client.logout()
        self.assertFalse(models.Game.objects.exists())

        create_url = reverse('create_game')
        response = self.client.get(create_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   create_url))

        response = self.client.post(
            create_url,
            {'name': "Foobar",
             'slug': "foobar",
             'description': "This *game* is foobared.",
             'markup_type': "markdown",
             'published': True,},
        )
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   create_url))
        self.assertFalse(models.Game.objects.exists())


class GameJoinViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.game = models.Game(
            name="Total War in Ulfland",
            slug="total-war-in-ulfland",
            host=self.user,
            description="This *game* is foobared.",
        )
        self.game.save()

    def test_join_game(self):
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

        join_url = reverse('game_join', kwargs={'game_slug': self.game.slug})
        response = self.client.get(join_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            join_url,
            {'name': "Gestalti",
             'plural_name': "Gestalti",
             'slug': "gestalti",
             'ambassador-name': "KonTiki"}
        )
        self.assertRedirects(response,
                             reverse('game_detail',
                                     kwargs={'slug': self.game.slug}))
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)
        race = models.Race.objects.get()
        self.assertEqual(race.name, "Gestalti")
        self.assertEqual(race.game, self.game)
        ambassador = models.Ambassador.objects.get()
        self.assertEqual(ambassador.name, "KonTiki")
        self.assertEqual(ambassador.race, race)
        self.assertEqual(ambassador.user, self.user)

    def test_anonymous_join(self):
        self.client.logout()
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

        join_url = reverse('game_join', kwargs={'game_slug': self.game.slug})
        response = self.client.get(join_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   join_url))

        response = self.client.post(
            join_url,
            {'name': "Gestalti",
             'plural_name': "Gestalti",
             'slug': "gestalti",
             'ambassador-name': "KonTiki"}
        )
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   join_url))
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

    def test_game_not_in_setup(self):
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())
        self.game.state = 'A'
        self.game.save()

        join_url = reverse('game_join', kwargs={'game_slug': self.game.slug})
        response = self.client.get(join_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            join_url,
            {'name': "Gestalti",
             'plural_name': "Gestalti",
             'slug': "gestalti",
             'ambassador-name': "KonTiki"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

    def test_join_same_slug(self):
        race = models.Race(game=self.game,
                           name='Gestalti',
                           plural_name='Gestalti',
                           slug='gestalti')
        race.save()
        ambassador = models.Ambassador(race=race,
                                       user=self.user,
                                       name="KonTiki")
        ambassador.save()

        join_url = reverse('game_join', kwargs={'game_slug': self.game.slug})
        response = self.client.post(
            join_url,
            {'name': "Histalti",
             'plural_name': "Histalti",
             'slug': "gestalti",
             'ambassador-name': "LonTiki"}
        )
        self.assertContains(response, "is already being used for this game.")
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)
