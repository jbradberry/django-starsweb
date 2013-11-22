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
