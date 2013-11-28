from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from django.conf import settings

from .. import models


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
        self.assertEqual(race.slug, "gestalti")
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
             'ambassador-name': "KonTiki"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())


class RaceUpdateViewTestCase(TestCase):
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
        race = models.Race(game=self.game,
                           name='Gestalti',
                           plural_name='Gestalti',
                           slug='gestalti')
        race.save()
        ambassador = models.Ambassador(race=race,
                                       user=self.user,
                                       name="KonTiki")
        ambassador.save()

    def test_view_form(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestalti")

    def test_successful_update(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.post(update_url,
                                    {'name': 'Gestalti2',
                                     'plural_name': 'Gestalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "KonTiki")

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().slug, "gestalti")
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_slug_change(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.post(update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Histalti")
        self.assertNotContains(response, "The Gestalti")
        self.assertContains(response, "KonTiki")

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().slug, "histalti")
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_name_too_long(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.post(update_url,
                                    {'name': 'A'*16,
                                     'plural_name': 'Gestalti'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 15 characters")
        self.assertEqual(models.Race.objects.count(), 1)
        race = models.Race.objects.get()
        self.assertEqual(race.slug, "gestalti")
        self.assertEqual(race.name, "Gestalti")

    def test_anonymous(self):
        self.client.logout()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   update_url))

        response = self.client.post(update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   update_url))
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().name, "Gestalti")

    def test_not_authorized(self):
        self.user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Race.objects.count(), 1)
        race = models.Race.objects.get()
        self.assertEqual(race.slug, "gestalti")
        self.assertEqual(race.name, "Gestalti")

    def test_race_does_not_exist(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'histalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 404)

    def test_game_does_not_exist(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('race_update',
                             kwargs={'game_slug': '500-years-after',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 404)


class AmbassadorUpdateViewTestCase(TestCase):
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
        race = models.Race(game=self.game,
                           name='Gestalti',
                           plural_name='Gestalti',
                           slug='gestalti')
        race.save()
        ambassador = models.Ambassador(race=race,
                                       user=self.user,
                                       name="KonTiki")
        ambassador.save()

    def test_view_form(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('ambassador_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KonTiki")

    def test_successful_update(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('ambassador_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.post(update_url,
                                    {'name': 'Kon-Tiki'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "Kon-Tiki")
        self.assertNotContains(response, "KonTiki")

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_name_too_long(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('ambassador_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.post(update_url,
                                    {'name': 'a'*129})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 128 characters")
        self.assertEqual(models.Ambassador.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.get().name, "KonTiki")

    def test_anonymous(self):
        self.client.logout()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('ambassador_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   update_url))

        response = self.client.post(update_url,
                                    {'name': 'Kon-Tiki'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   update_url))
        self.assertEqual(models.Ambassador.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.get().name, "KonTiki")

    def test_not_authorized(self):
        self.user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('ambassador_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(update_url,
                                    {'name': 'Kon-Tiki'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Ambassador.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.get().name, "KonTiki")

    def test_race_does_not_exist(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('ambassador_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'histalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 404)

    def test_game_does_not_exist(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        update_url = reverse('ambassador_update',
                             kwargs={'game_slug': '500-years-after',
                                     'race_slug': 'gestalti'})
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 404)
