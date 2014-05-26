from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import File
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.html import escape
from django.test import TestCase
from django.conf import settings

import os

from .. import models

PATH = os.path.dirname(__file__)


class GameDetailViewTestCase(TestCase):
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
        self.race1 = models.Race(game=self.game,
                                 name='Gestalti',
                                 plural_name='Gestalti',
                                 slug='gestalti')
        self.race1.save()
        self.race2 = models.Race(game=self.game,
                                 name='Phizz',
                                 plural_name='Phizz',
                                 slug='phizz')
        self.race2.save()
        self.race3 = models.Race(game=self.game,
                                 name='SSG',
                                 plural_name='SSG',
                                 slug='ssg')
        self.race3.save()

        self.detail_url = reverse('game_detail',
                                  kwargs={'slug': self.game.slug})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_no_scores(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, "Total War in Ulfland")
        self.assertContains(response, "This <em>game</em> is foobared.")
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "The Phizz")
        self.assertContains(response, "The SSG")
        self.assertIn('races', response.context)

        races = zip(*response.context['races'])
        self.assertEqual(races[0], (self.race1, self.race2, self.race3))
        self.assertEqual(races[1], (None, None, None))

    def test_player_numbers_but_no_scores(self):
        self.race1.player_number = 1
        self.race1.save()
        self.race2.player_number = 0
        self.race2.save()
        self.race3.player_number = 2
        self.race3.save()

        response = self.client.get(self.detail_url)
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "The Phizz")
        self.assertContains(response, "The SSG")

        races = zip(*response.context['races'])
        self.assertEqual(races[0], (self.race2, self.race1, self.race3))
        self.assertEqual(races[1], (None, None, None))

    def test_all_with_scores(self):
        self.race1.player_number = 1
        self.race1.save()
        self.race2.player_number = 0
        self.race2.save()
        self.race3.player_number = 2
        self.race3.save()
        self.game.state = 'A'
        self.game.save()
        turn = self.game.turns.create(year=2401)
        turn.scores.create(race=self.race1, section=models.Score.SCORE,
                           value=247)
        turn.scores.create(race=self.race2, section=models.Score.SCORE,
                           value=430)
        turn.scores.create(race=self.race3, section=models.Score.SCORE,
                           value=576)

        response = self.client.get(self.detail_url)
        self.assertContains(response, "Year 2401")
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "The Phizz")
        self.assertContains(response, "The SSG")

        races = zip(*response.context['races'])
        self.assertEqual(races[0], (self.race3, self.race2, self.race1))
        self.assertEqual(races[1], (576, 430, 247))

        self.assertContains(response, "<td>576</td>")
        self.assertContains(response, "<td>430</td>")
        self.assertContains(response, "<td>247</td>")

    def test_with_dead_race(self):
        self.race1.player_number = 1
        self.race1.save()
        self.race2.player_number = 0
        self.race2.save()
        self.race3.player_number = 2
        self.race3.save()
        self.game.state = 'A'
        self.game.save()
        turn = self.game.turns.create(year=2401)
        turn.scores.create(race=self.race1, section=models.Score.SCORE,
                           value=5097)
        turn.scores.create(race=self.race2, section=models.Score.SCORE,
                           value=6702)
        turn.scores.create(race=self.race3, section=models.Score.SCORE,
                           value=0)

        response = self.client.get(self.detail_url)
        self.assertContains(response, "Year 2401")
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "The Phizz")
        self.assertContains(response, "The SSG")

        races = zip(*response.context['races'])
        self.assertEqual(races[0], (self.race2, self.race1, self.race3))
        self.assertEqual(races[1], (6702, 5097, 0))

        self.assertContains(response, "<td>6702</td>")
        self.assertContains(response, "<td>5097</td>")
        self.assertContains(response, "<td>0</td>")

    def test_with_multiple_turns(self):
        self.race1.player_number = 1
        self.race1.save()
        self.race2.player_number = 0
        self.race2.save()
        self.race3.player_number = 2
        self.race3.save()
        self.game.state = 'A'
        self.game.save()
        turn = self.game.turns.create(year=2401)
        turn.scores.create(race=self.race1, section=models.Score.SCORE,
                           value=247)
        turn.scores.create(race=self.race2, section=models.Score.SCORE,
                           value=430)
        turn.scores.create(race=self.race3, section=models.Score.SCORE,
                           value=576)

        turn = self.game.turns.create(year=2402)
        turn.scores.create(race=self.race1, section=models.Score.SCORE,
                           value=5097)
        turn.scores.create(race=self.race2, section=models.Score.SCORE,
                           value=6702)
        turn.scores.create(race=self.race3, section=models.Score.SCORE,
                           value=3592)

        response = self.client.get(self.detail_url)
        self.assertContains(response, "Year 2402")
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "The Phizz")
        self.assertContains(response, "The SSG")

        races = zip(*response.context['races'])
        self.assertEqual(races[0], (self.race2, self.race1, self.race3))
        self.assertEqual(races[1], (6702, 5097, 3592))

        self.assertContains(response, "<td>6702</td>")
        self.assertContains(response, "<td>5097</td>")
        self.assertContains(response, "<td>3592</td>")
        self.assertNotContains(response, "<td>576</td>")
        self.assertNotContains(response, "<td>430</td>")
        self.assertNotContains(response, "<td>247</td>")


class GameCreateViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

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


class GameMapDownloadTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.game = models.Game(
            name="Total War in Ulfland",
            slug="total-war-in-ulfland",
            host=self.user,
            state='A',
            description="This *game* is foobared.",
        )
        self.game.save()

        starsfile = models.StarsFile(upload_user=self.user, type='xy')
        starsfile.save()
        with open(os.path.join(PATH, 'files', 'ulf_war.xy')) as f:
            starsfile.file.save('ulf_war.xy', File(f))

        self.game.mapfile = starsfile
        self.game.save()

        self.download_url = reverse('game_mapdownload',
                                    kwargs={'game_slug': self.game.slug})

    def test_success(self):
        self.assertIsNotNone(self.game.mapfile)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="total-wa.xy"')
        self.assertEqual(response['Content-length'], '3864')

    def test_anonymous(self):
        # We'll allow it.
        self.client.logout()
        self.assertIsNotNone(self.game.mapfile)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="total-wa.xy"')
        self.assertEqual(response['Content-length'], '3864')

    def test_no_mapfile_attached(self):
        self.game.mapfile = None
        self.game.save()
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 404)

    def test_does_not_exist(self):
        download_url = reverse('game_mapdownload',
                               kwargs={'game_slug': '500-years-after'})
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 404)


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

        self.join_url = reverse('game_join',
                                kwargs={'game_slug': self.game.slug})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_join_game(self):
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

        response = self.client.get(self.join_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            self.join_url,
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

        response = self.client.get(self.join_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.join_url))

        response = self.client.post(
            self.join_url,
            {'name': "Gestalti",
             'plural_name': "Gestalti",
             'ambassador-name': "KonTiki"}
        )
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.join_url))
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

    def test_game_active(self):
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())
        self.game.state = 'A'
        self.game.save()

        response = self.client.get(self.join_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            self.join_url,
            {'name': "Gestalti",
             'plural_name': "Gestalti",
             'ambassador-name': "KonTiki"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

    def test_game_paused(self):
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())
        self.game.state = 'P'
        self.game.save()

        response = self.client.get(self.join_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            self.join_url,
            {'name': "Gestalti",
             'plural_name': "Gestalti",
             'ambassador-name': "KonTiki"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())

    def test_game_finished(self):
        self.assertFalse(models.Race.objects.exists())
        self.assertFalse(models.Ambassador.objects.exists())
        self.game.state = 'F'
        self.game.save()

        response = self.client.get(self.join_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            self.join_url,
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
        self.race = models.Race(game=self.game,
                                name='Gestalti',
                                plural_name='Gestalti',
                                slug='gestalti')
        self.race.save()
        self.ambassador = models.Ambassador(race=self.race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()
        self.update_url = reverse('race_update',
                                  kwargs={'game_slug': 'total-war-in-ulfland',
                                          'race_slug': 'gestalti'})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gestalti")

        response = self.client.post(self.update_url,
                                    {'name': 'Gestalti2',
                                     'plural_name': 'Gestalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "KonTiki")
        self.assertContains(
            response,
            "The race name and plural name have successfully been changed.")

        self.assertEqual(models.Race.objects.count(), 1)
        race = models.Race.objects.get()

        self.assertIsNone(race.racefile)
        self.assertNotContains(
            response,
            escape("The attached race file's name or plural name has been"
                   " adjusted to match your race's name and plural name.")
        )

        self.assertEqual(race.slug, "gestalti")
        self.assertEqual(race.name, "Gestalti2")
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_slug_change(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.post(self.update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Histalti")
        self.assertNotContains(response, "The Gestalti")
        self.assertContains(response, "KonTiki")
        self.assertContains(
            response,
            "The race name and plural name have successfully been changed.")

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().slug, "histalti")
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_change_to_racefile(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        starsfile = models.StarsFile(upload_user=self.user, type='r')
        starsfile.save()
        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            starsfile.file.save('foo.r1', File(f))

        self.race.racefile = starsfile
        self.race.save()

        old_path = starsfile.file.path

        response = self.client.post(self.update_url,
                                    {'name': 'Gestalti2',
                                     'plural_name': 'Gestalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            escape("The attached race file's name or plural name has been"
                   " adjusted to match your race's name and plural name.")
        )
        self.assertContains(
            response,
            "The race name and plural name have successfully been changed.")

        starsfile = models.StarsFile.objects.get()
        new_path = starsfile.file.path
        with open(new_path) as f:
            new_file = f.read()
        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            old_file = f.read()

        self.assertNotEqual(new_file, old_file,
                            msg="File contents unexpectedly equal.")
        self.assertNotEqual(new_path, old_path)

        # this is less than ideal, but we don't want extra files
        # accumulating
        try:
            os.remove(old_path)
        except Exception:
            pass

    def test_game_active(self):
        self.game.state = 'A'
        self.game.save()

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().slug, "gestalti")

    def test_game_paused(self):
        self.game.state = 'P'
        self.game.save()

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().slug, "gestalti")

    def test_game_finished(self):
        self.game.state = 'F'
        self.game.save()

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().slug, "gestalti")

    def test_name_too_long(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.post(self.update_url,
                                    {'name': 'A'*16,
                                     'plural_name': 'Gestalti'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 15 characters")
        self.assertEqual(models.Race.objects.count(), 1)
        race = models.Race.objects.get()
        self.assertEqual(race.slug, "gestalti")
        self.assertEqual(race.name, "Gestalti")

    def test_name_not_cp1252(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.post(self.update_url,
                                    {'name': u'\u2603',
                                     'plural_name': 'Gestalti'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            "Race name is restricted to the cp1252/latin1"
                            " character set.")
        self.assertEqual(models.Race.objects.count(), 1)
        race = models.Race.objects.get()
        self.assertEqual(race.slug, "gestalti")
        self.assertEqual(race.name, "Gestalti")

    def test_anonymous(self):
        self.client.logout()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.update_url))

        response = self.client.post(self.update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.update_url))
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().name, "Gestalti")

    def test_not_authorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
                                    {'name': 'Histalti',
                                     'plural_name': 'Histalti'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Race.objects.count(), 1)
        race = models.Race.objects.get()
        self.assertEqual(race.slug, "gestalti")
        self.assertEqual(race.name, "Gestalti")

    def test_ambassador_no_longer_active(self):
        self.ambassador.active = False
        self.ambassador.save()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
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
        self.ambassador = models.Ambassador(race=race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()

        self.update_url = reverse('ambassador_update',
                                  kwargs={'game_slug': 'total-war-in-ulfland',
                                          'race_slug': 'gestalti'})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KonTiki")

        response = self.client.post(self.update_url,
                                    {'name': 'Kon-Tiki'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "Kon-Tiki")
        self.assertNotContains(response, "KonTiki")

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_game_active(self):
        self.game.state = 'A'
        self.game.save()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KonTiki")

        response = self.client.post(self.update_url,
                                    {'name': 'Kon-Tiki'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "Kon-Tiki")
        self.assertNotContains(response, "KonTiki")

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_game_paused(self):
        self.game.state = 'P'
        self.game.save()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KonTiki")

        response = self.client.post(self.update_url,
                                    {'name': 'Kon-Tiki'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Gestalti")
        self.assertContains(response, "Kon-Tiki")
        self.assertNotContains(response, "KonTiki")

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_game_finished(self):
        self.game.state = 'F'
        self.game.save()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
                                    {'name': 'Kon-Tiki'},
                                    follow=True)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Race.objects.get().name, "Gestalti")
        self.assertEqual(models.Ambassador.objects.count(), 1)

    def test_name_too_long(self):
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.post(self.update_url,
                                    {'name': 'a'*129})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 128 characters")
        self.assertEqual(models.Ambassador.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.get().name, "KonTiki")

    def test_anonymous(self):
        self.client.logout()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.update_url))

        response = self.client.post(self.update_url,
                                    {'name': 'Kon-Tiki'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.update_url))
        self.assertEqual(models.Ambassador.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.get().name, "KonTiki")

    def test_not_authorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
                                    {'name': 'Kon-Tiki'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.Ambassador.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.get().name, "KonTiki")

    def test_ambassador_no_longer_active(self):
        self.ambassador.active = False
        self.ambassador.save()
        self.assertEqual(models.Race.objects.count(), 1)
        self.assertEqual(models.Ambassador.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
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


class RaceDashboardViewTestCase(TestCase):
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
        self.race = models.Race(game=self.game,
                                name='Gestalti',
                                plural_name='Gestalti',
                                slug='gestalti')
        self.race.save()
        self.ambassador = models.Ambassador(race=self.race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()
        self.url_kwargs = {'game_slug': 'total-war-in-ulfland',
                           'race_slug': 'gestalti'}
        self.dashboard_url = reverse('race_dashboard',
                                     kwargs=self.url_kwargs)

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_setup_state(self):
        self.assertEqual(self.game.state, 'S')

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('race_form', response.context)
        self.assertIn('ambassador_form', response.context)
        self.assertIn('raceupload_form', response.context)
        self.assertIn('racechoose_form', response.context)

        self.assertContains(response, reverse('race_update',
                                              kwargs=self.url_kwargs))
        self.assertContains(response, reverse('ambassador_update',
                                              kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_download',
                                                 kwargs=self.url_kwargs))
        self.assertContains(response, reverse('race_upload',
                                              kwargs=self.url_kwargs))
        self.assertContains(response, reverse('race_bind',
                                              kwargs=self.url_kwargs))

        self.assertContains(response, "<b>Player Number:</b> N/A")

    def test_game_active(self):
        self.game.state = 'A'
        self.game.save()
        self.race.player_number = 0
        self.race.save()

        self.assertEqual(self.game.state, 'A')

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('race_form', response.context)
        self.assertIn('ambassador_form', response.context)
        self.assertNotIn('raceupload_form', response.context)
        self.assertNotIn('racechoose_form', response.context)

        self.assertNotContains(response, reverse('race_update',
                                                 kwargs=self.url_kwargs))
        self.assertContains(response, reverse('ambassador_update',
                                              kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_download',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_upload',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_bind',
                                                 kwargs=self.url_kwargs))

        self.assertContains(response, "<b>Player Number:</b> 1")

    def test_game_paused(self):
        self.game.state = 'P'
        self.game.save()

        self.assertEqual(self.game.state, 'P')

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('race_form', response.context)
        self.assertIn('ambassador_form', response.context)
        self.assertNotIn('raceupload_form', response.context)
        self.assertNotIn('racechoose_form', response.context)

        self.assertNotContains(response, reverse('race_update',
                                                 kwargs=self.url_kwargs))
        self.assertContains(response, reverse('ambassador_update',
                                              kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_download',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_upload',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_bind',
                                                 kwargs=self.url_kwargs))

    def test_game_finished(self):
        self.game.state = 'F'
        self.game.save()

        self.assertEqual(self.game.state, 'F')

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('race_form', response.context)
        self.assertNotIn('ambassador_form', response.context)
        self.assertNotIn('raceupload_form', response.context)
        self.assertNotIn('racechoose_form', response.context)

        self.assertNotContains(response, reverse('race_update',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('ambassador_update',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_download',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_upload',
                                                 kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_bind',
                                                 kwargs=self.url_kwargs))

    def test_userrace_with_no_racefile(self):
        userrace = self.user.racepool.create(identifier="Gestalti v1")
        self.assertFalse(models.UserRace.objects.filter(racefile__isnull=False))

        try:
            response = self.client.get(self.dashboard_url)
        except Exception as e:
            self.fail(e)

        self.assertEqual(response.status_code, 200)
        self.assertIn('race_form', response.context)
        self.assertIn('ambassador_form', response.context)
        self.assertIn('raceupload_form', response.context)
        self.assertIn('racechoose_form', response.context)

        self.assertContains(response, reverse('race_update',
                                              kwargs=self.url_kwargs))
        self.assertContains(response, reverse('ambassador_update',
                                              kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_download',
                                                 kwargs=self.url_kwargs))
        self.assertContains(response, reverse('race_upload',
                                              kwargs=self.url_kwargs))
        self.assertContains(response, reverse('race_bind',
                                              kwargs=self.url_kwargs))
        self.assertNotContains(response, "Gestalti v1")

    def test_userrace_with_racefile(self):
        userrace = self.user.racepool.create(identifier="Gestalti v1")
        starsfile = models.StarsFile(upload_user=self.user, type='r')
        starsfile.save()
        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            starsfile.file.save('foo.r1', File(f))
        userrace.racefile = starsfile
        userrace.save()

        self.assertTrue(models.UserRace.objects.filter(racefile__isnull=False))

        try:
            response = self.client.get(self.dashboard_url)
        except Exception as e:
            self.fail(e)

        self.assertEqual(response.status_code, 200)
        self.assertIn('race_form', response.context)
        self.assertIn('ambassador_form', response.context)
        self.assertIn('raceupload_form', response.context)
        self.assertIn('racechoose_form', response.context)

        self.assertContains(response, reverse('race_update',
                                              kwargs=self.url_kwargs))
        self.assertContains(response, reverse('ambassador_update',
                                              kwargs=self.url_kwargs))
        self.assertNotContains(response, reverse('race_download',
                                                 kwargs=self.url_kwargs))
        self.assertContains(response, reverse('race_upload',
                                              kwargs=self.url_kwargs))
        self.assertContains(response, reverse('race_bind',
                                              kwargs=self.url_kwargs))
        self.assertContains(response, "Gestalti v1")

    def test_game_does_not_exist(self):
        dashboard_url = reverse('race_dashboard',
                                kwargs={'game_slug': '500-years-after',
                                        'race_slug': 'gestalti'})
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 404)

    def test_race_does_not_exist(self):
        dashboard_url = reverse('race_dashboard',
                                kwargs={'game_slug': 'total-war-in-ulfland',
                                        'race_slug': 'histalti'})
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 404)

    def test_not_authorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_ambassador_no_longer_active(self):
        self.ambassador.active = False
        self.ambassador.save()

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous(self):
        self.client.logout()

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.dashboard_url))


class UserDashboardTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.starsfile1 = models.StarsFile(upload_user=self.user,
                                           type='r')
        self.starsfile1.save()
        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            self.starsfile1.file.save('foo.r1', File(f))

        self.starsfile2 = models.StarsFile(upload_user=self.user,
                                           type='r')
        self.starsfile2.save()
        with open(os.path.join(PATH, 'files', 'ssg.r1')) as f:
            self.starsfile2.file.save('foo.r1', File(f))

        self.userrace1 = models.UserRace(user=self.user,
                                         identifier="Gestalti v1",
                                         racefile=self.starsfile1)
        self.userrace1.save()

        self.userrace2 = models.UserRace(user=self.user,
                                         identifier="SSG v1",
                                         racefile=self.starsfile2)
        self.userrace2.save()

        self.game = models.Game(
            name="Total War in Ulfland",
            slug="total-war-in-ulfland",
            host=self.user,
            description="This *game* is foobared.",
        )
        self.game.save()
        self.race = models.Race(game=self.game,
                                name='Gestalti',
                                plural_name='Gestalti',
                                slug='gestalti',
                                official_racefile=self.starsfile1)
        self.race.save()
        self.ambassador = models.Ambassador(race=self.race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()

        self.dashboard_url = reverse('user_dashboard')

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Gestalti v1")
        self.assertContains(response, "SSG v1")
        self.assertIn('userraces', response.context)
        self.assertIn('races', response.context)
        self.assertEqual(len(response.context['userraces']), 2)
        self.assertEqual(len(response.context['races']), 1)

        self.assertContains(
            response,
            reverse('race_download',
                    kwargs={'game_slug': self.game.slug,
                            'race_slug': self.race.slug}))

        self.assertContains(
            response,
            reverse('userrace_download',
                    kwargs={'pk': self.userrace1.pk}))

        self.assertContains(
            response,
            reverse('userrace_download',
                    kwargs={'pk': self.userrace2.pk}))

    def test_userrace_without_file(self):
        self.userrace2.racefile = None
        self.userrace2.save()

        try:
            response = self.client.get(self.dashboard_url)
        except Exception as e:
            self.fail(e)

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Gestalti v1")
        self.assertContains(response, "SSG v1")
        self.assertIn('userraces', response.context)
        self.assertIn('races', response.context)
        self.assertEqual(len(response.context['userraces']), 2)
        self.assertEqual(len(response.context['races']), 1)

        self.assertContains(
            response,
            reverse('race_download',
                    kwargs={'game_slug': self.game.slug,
                            'race_slug': self.race.slug}))

        self.assertContains(
            response,
            reverse('userrace_download',
                    kwargs={'pk': self.userrace1.pk}))

        self.assertNotContains(
            response,
            reverse('userrace_download',
                    kwargs={'pk': self.userrace2.pk}))

    def test_anonymous(self):
        self.client.logout()

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.dashboard_url))


class UserRaceCreateTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.create_url = reverse('userrace_create')

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_success(self):
        self.assertEqual(models.UserRace.objects.count(), 0)

        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        response = self.client.post(self.create_url,
                                    {'identifier': "Gestalti v1"})
        self.assertEqual(response.status_code, 302)

        self.assertEqual(models.UserRace.objects.count(), 1)
        userrace = models.UserRace.objects.get()
        self.assertEqual(userrace.user, self.user)
        self.assertEqual(userrace.identifier, "Gestalti v1")

    def test_anonymous(self):
        self.client.logout()

        self.assertEqual(models.UserRace.objects.count(), 0)

        response = self.client.get(self.create_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.create_url))

        response = self.client.post(self.create_url,
                                    {'identifier': "Gestalti v1"})
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.create_url))

        self.assertEqual(models.UserRace.objects.count(), 0)

    def test_already_exists(self):
        models.UserRace.objects.create(user=self.user,
                                       identifier="Gestalti v1")
        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        response = self.client.post(self.create_url,
                                    {'identifier': "Gestalti v1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "User race with this User and Identifier already exists.")
        self.assertEqual(models.UserRace.objects.count(), 1)


class UserRaceUpdateTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.userrace = models.UserRace(user=self.user,
                                        identifier="Gestalti v1")
        self.userrace.save()

        self.update_url = reverse('userrace_update',
                                  kwargs={'pk': self.userrace.pk})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_success(self):
        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertContains(response, "Gestalti v1")

        response = self.client.post(self.update_url,
                                    {'identifier': "Histalti"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.UserRace.objects.count(), 1)
        userrace = models.UserRace.objects.get()
        self.assertEqual(userrace.user, self.user)
        self.assertEqual(userrace.identifier, "Histalti")

    def test_unauthorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.update_url,
                                    {'identifier': "Histalti"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.UserRace.objects.count(), 1)
        userrace = models.UserRace.objects.get()
        self.assertEqual(userrace.user, self.user)
        self.assertEqual(userrace.identifier, "Gestalti v1")

    def test_anonymous(self):
        self.client.logout()

        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(self.update_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.update_url))

        response = self.client.post(self.update_url,
                                    {'identifier': "Histalti"})
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.update_url))
        self.assertEqual(models.UserRace.objects.count(), 1)
        userrace = models.UserRace.objects.get()
        self.assertEqual(userrace.user, self.user)
        self.assertEqual(userrace.identifier, "Gestalti v1")

    def test_does_not_exist(self):
        update_url = reverse('userrace_update',
                             kwargs={'pk': self.userrace.pk + 1})

        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.post(update_url,
                                    {'identifier': "Histalti"})
        self.assertEqual(response.status_code, 404)

        self.assertEqual(models.UserRace.objects.count(), 1)
        userrace = models.UserRace.objects.get()
        self.assertEqual(userrace.user, self.user)
        self.assertEqual(userrace.identifier, "Gestalti v1")

    def test_already_exists(self):
        models.UserRace.objects.create(user=self.user,
                                       identifier="Histalti")
        self.assertEqual(models.UserRace.objects.count(), 2)

        response = self.client.post(self.update_url,
                                    {'identifier': "Histalti"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "User race with this User and Identifier already exists.")

        self.assertEqual(models.UserRace.objects.count(), 2)
        userrace = models.UserRace.objects.get(pk=self.userrace.pk)
        self.assertEqual(userrace.user, self.user)
        self.assertEqual(userrace.identifier, "Gestalti v1")


class UserRaceDeleteTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.userrace = models.UserRace(user=self.user,
                                        identifier="Gestalti v1")
        self.userrace.save()

        self.delete_url = reverse('userrace_delete',
                                  kwargs={'pk': self.userrace.pk})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_success(self):
        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Are you sure you want to delete")

        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(models.UserRace.objects.count(), 0)

    def test_unauthorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(models.UserRace.objects.count(), 1)

    def test_anonymous(self):
        self.client.logout()

        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(self.delete_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.delete_url))

        response = self.client.post(self.delete_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.delete_url))

        self.assertEqual(models.UserRace.objects.count(), 1)

    def test_does_not_exist(self):
        delete_url = reverse('userrace_delete',
                             kwargs={'pk': self.userrace.pk + 1})

        self.assertEqual(models.UserRace.objects.count(), 1)

        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 404)

        self.assertEqual(models.UserRace.objects.count(), 1)


class RaceFileBindTestCase(TestCase):
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
        self.race = models.Race(game=self.game,
                                name='Gestalti',
                                plural_name='Gestalti',
                                slug='gestalti')
        self.race.save()
        self.ambassador = models.Ambassador(race=self.race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()
        self.starsfile = models.StarsFile(upload_user=self.user,
                                          type='r')
        self.starsfile.save()
        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            self.starsfile.file.save('foo.r1', File(f))
        self.userrace = models.UserRace(user=self.user,
                                        identifier="Gestalti v1",
                                        racefile=self.starsfile)
        self.userrace.save()

        self.bind_url = reverse('race_bind',
                                kwargs={'game_slug': 'total-war-in-ulfland',
                                        'race_slug': 'gestalti'})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        race = models.Race.objects.get()
        self.assertIsNone(race.racefile)

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        race = models.Race.objects.get()
        starsfile = models.StarsFile.objects.get(pk=self.starsfile.pk)
        self.assertIsNotNone(race.racefile)
        self.assertNotEqual(race.racefile.pk, starsfile.pk)
        self.assertNotEqual(race.racefile.file.path, starsfile.file.path)

        with open(race.racefile.file.path) as f:
            data_new = f.read()
        with open(starsfile.file.path) as f:
            data_old = f.read()
        self.assertEqual(data_new, data_old,
                         msg="File contents unexpectedly not equal.")

        self.assertContains(response,
                            "The race file has successfully been attached.")
        self.assertNotContains(response,
                               "name or plural name has been adjusted to match"
                               " your race")

    def test_unbind_race_file(self):
        race = models.Race.objects.get()
        race.racefile = self.starsfile
        race.save()
        self.assertIsNotNone(race.racefile)

        response = self.client.post(self.bind_url,
                                    {'racefile': ''},
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "This field is required.")
        self.assertContains(response,
                            "The race file has successfully been unattached.")

        race = models.Race.objects.get()
        self.assertIsNone(race.racefile)

    def test_userrace_without_racefile(self):
        self.userrace.racefile = None
        self.userrace.save()

        try:
            response = self.client.get(self.bind_url)
        except Exception as e:
            self.fail(e)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertNotContains(response, "Gestalti v1")

    def test_name_change(self):
        race = models.Race.objects.get()
        self.assertIsNone(race.racefile)

        starsfile = models.StarsFile(upload_user=self.user,
                                     type='r')
        starsfile.save()
        with open(os.path.join(PATH, 'files', 'ssg.r1')) as f:
            starsfile.file.save('foo.r2', File(f))
        userrace = models.UserRace(user=self.user,
                                   identifier="SSG",
                                   racefile=starsfile)
        userrace.save()

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        response = self.client.post(self.bind_url,
                                    {'racefile': starsfile.pk},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        race = models.Race.objects.get()
        starsfile = models.StarsFile.objects.get(pk=self.starsfile.pk)
        self.assertIsNotNone(race.racefile)
        self.assertNotEqual(race.racefile.pk, starsfile.pk)
        self.assertNotEqual(race.racefile.file.path, starsfile.file.path)

        with open(race.racefile.file.path) as f:
            data_new = f.read()
        with open(starsfile.file.path) as f:
            data_old = f.read()
        self.assertNotEqual(data_new, data_old,
                            msg="File contents unexpectedly equal.")

        self.assertContains(response,
                            "The race file has successfully been attached.")
        self.assertContains(response,
                            "name or plural name has been adjusted to match"
                            " your race")

    def test_unauthorized(self):
        self.assertIsNone(self.race.racefile)

        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        self.userrace.user = user
        self.userrace.save()

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 403)

        self.assertIsNone(self.race.racefile)

    def test_ambassador_no_longer_active(self):
        self.assertIsNone(self.race.racefile)

        self.ambassador.active = False
        self.ambassador.save()

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 403)

        self.assertIsNone(self.race.racefile)

    def test_anonymous(self):
        self.assertIsNone(self.race.racefile)

        self.client.logout()

        response = self.client.get(self.bind_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.bind_url))

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.bind_url))

        self.assertIsNone(self.race.racefile)

    def test_not_authorized_for_userrace(self):
        self.assertIsNone(self.race.racefile)

        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')
        self.ambassador.user = user
        self.ambassador.save()

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            "That choice is not one of the available choices.")

        self.assertIsNone(self.race.racefile)

    def test_game_active(self):
        self.assertIsNone(self.race.racefile)

        self.game.state = 'A'
        self.game.save()

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 403)

        self.assertIsNone(self.race.racefile)

    def test_game_paused(self):
        self.assertIsNone(self.race.racefile)

        self.game.state = 'P'
        self.game.save()

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 403)

        self.assertIsNone(self.race.racefile)

    def test_game_finished(self):
        self.assertIsNone(self.race.racefile)

        self.game.state = 'F'
        self.game.save()

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 403)

        self.assertIsNone(self.race.racefile)

    def test_race_does_not_exist(self):
        self.assertIsNone(self.race.racefile)

        bind_url = reverse('race_bind',
                           kwargs={'game_slug': 'total-war-in-ulfland',
                                   'race_slug': 'histalti'})
        response = self.client.get(bind_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.post(bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 404)

        self.assertIsNone(self.race.racefile)

    def test_game_does_not_exist(self):
        self.assertIsNone(self.race.racefile)

        bind_url = reverse('race_update',
                           kwargs={'game_slug': '500-years-after',
                                   'race_slug': 'gestalti'})
        response = self.client.get(bind_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.post(bind_url,
                                    {'racefile': self.starsfile.pk})
        self.assertEqual(response.status_code, 404)

        self.assertIsNone(self.race.racefile)

    def test_userrace_does_not_exist(self):
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.bind_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        response = self.client.post(self.bind_url,
                                    {'racefile': self.starsfile.pk + 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            "That choice is not one of the available choices.")

        self.assertIsNone(self.race.racefile)


class UserRaceDownloadTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.starsfile = models.StarsFile(upload_user=self.user,
                                          type='r',
                                          file=SimpleUploadedFile("file.r1", "test"))
        self.starsfile.save()
        self.userrace = models.UserRace(user=self.user,
                                        identifier="Gestalti v1",
                                        racefile=self.starsfile)
        self.userrace.save()
        self.download_url = reverse('userrace_download',
                                    kwargs={'pk': self.userrace.pk})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="gestalti.r1"')
        self.assertEqual(response['Content-length'], '4')

    def test_unauthorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response,
                            "Not authorized to download this race file.",
                            status_code=403)

    def test_anonymous(self):
        self.client.logout()

        response = self.client.get(self.download_url)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.download_url))

    def test_does_not_exist(self):
        download_url = reverse('userrace_download',
                               kwargs={'pk': self.userrace.pk + 1})

        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 404)


class UserRaceUploadTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='password')
        self.client.login(username='admin', password='password')

        self.userrace = models.UserRace(user=self.user,
                                        identifier="Gestalti v1")
        self.userrace.save()

        self.upload_url = reverse('userrace_upload',
                                  kwargs={'pk': self.userrace.pk})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f},
                                        follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            "The race file has successfully been uploaded.")
        self.assertNotContains(response,
                               escape("name had the word 'The' before it."))
        self.assertEqual(models.StarsFile.objects.count(), 1)
        self.assertIsNotNone(models.UserRace.objects.get().racefile)

    def test_unauthorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

    def test_anonymous(self):
        self.client.logout()

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.upload_url))

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.upload_url))

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

    def test_file_not_stars_file(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

        with open(os.path.join(PATH, '__init__.py')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not a valid Stars race file.")
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

    def test_file_not_race_file(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

        with open(os.path.join(PATH, 'files', 'ulf_war.xy')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not a valid Stars race file.")
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

    def test_userrace_does_not_exist(self):
        self.assertEqual(models.UserRace.objects.count(), 1)
        upload_url = reverse('userrace_upload',
                             kwargs={'pk': self.userrace.pk + 1})

        response = self.client.get(upload_url)
        self.assertEqual(response.status_code, 404)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(upload_url, {'file': f})
        self.assertEqual(response.status_code, 404)

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

    def test_prepended_the_in_race_name(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.UserRace.objects.get().racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)

        with open(os.path.join(PATH, 'files', 'ssg.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f},
                                        follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            "The race file has successfully been uploaded.")
        self.assertContains(response,
                            escape("name had the word 'The' before it."))
        self.assertEqual(models.StarsFile.objects.count(), 1)
        self.assertIsNotNone(models.UserRace.objects.get().racefile)


class RaceFileDownloadTestCase(TestCase):
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
        self.starsfile = models.StarsFile(upload_user=self.user,
                                          type='r',
                                          file=SimpleUploadedFile("file.r1", "test"))
        self.starsfile.save()
        self.race = models.Race(game=self.game,
                                name='Gestalti',
                                plural_name='Gestalti',
                                slug='gestalti',
                                racefile=self.starsfile)
        self.race.save()
        self.ambassador = models.Ambassador(race=self.race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()

        self.download_url = reverse('race_download',
                                    kwargs={'game_slug': 'total-war-in-ulfland',
                                            'race_slug': 'gestalti'})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        self.assertEqual(models.StarsFile.objects.filter(type='r').count(), 1)

        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="gestalti.r1"')
        self.assertEqual(response['Content-length'], '4')

    def test_unauthorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        self.assertEqual(models.StarsFile.objects.filter(type='r').count(), 1)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response,
                            "Not authorized to download files for this race.",
                            status_code=403)

    def test_ambassador_no_longer_active(self):
        # allow players who are no longer active in a game to still
        # download the race file.
        self.ambassador.active = False
        self.ambassador.save()

        self.assertEqual(models.StarsFile.objects.filter(type='r').count(), 1)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="gestalti.r1"')
        self.assertEqual(response['Content-length'], '4')

    def test_anonymous(self):
        self.client.logout()

        self.assertEqual(models.StarsFile.objects.filter(type='r').count(), 1)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.download_url))

    def test_game_does_not_exist(self):
        self.assertEqual(models.StarsFile.objects.filter(type='r').count(), 1)

        download_url = reverse('race_download',
                               kwargs={'game_slug': '500-years-after',
                                       'race_slug': 'gestalti'})

        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 404)

    def test_race_does_not_exist(self):
        self.assertEqual(models.StarsFile.objects.filter(type='r').count(), 1)

        download_url = reverse('race_download',
                               kwargs={'game_slug': 'total-war-in-ulfland',
                                       'race_slug': 'histalti'})

        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 404)


class RaceFileUploadTestCase(TestCase):
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
        self.race = models.Race(game=self.game,
                                name='Gestalti',
                                plural_name='Gestalti',
                                slug='gestalti')
        self.race.save()
        self.ambassador = models.Ambassador(race=self.race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()

        self.upload_url = reverse('race_upload',
                                  kwargs={'game_slug': 'total-war-in-ulfland',
                                          'race_slug': 'gestalti'})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.StarsFile.objects.count(), 1)
        self.assertIsNotNone(models.Race.objects.get().racefile)

    def test_unauthorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_ambassador_no_longer_active(self):
        self.ambassador.active = False
        self.ambassador.save()

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_anonymous(self):
        self.client.logout()

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.upload_url))

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.upload_url))
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_game_in_active_state(self):
        self.game.state = 'A'
        self.game.save()

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_game_in_paused_state(self):
        self.game.state = 'P'
        self.game.save()

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_game_in_finished_state(self):
        self.game.state = 'F'
        self.game.save()

        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 403)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_file_not_stars_file(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

        with open(os.path.join(PATH, '__init__.py')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not a valid Stars race file.")
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_file_not_race_file(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

        with open(os.path.join(PATH, 'files', 'ulf_war.xy')) as f:
            response = self.client.post(self.upload_url, {'file': f})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not a valid Stars race file.")
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

    def test_race_file_with_different_name(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(models.Race.objects.get().racefile)

        with open(os.path.join(PATH, 'files', 'ssg.r1')) as f:
            response = self.client.post(self.upload_url, {'file': f},
                                        follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            "name or plural name has been adjusted to match")
        self.assertEqual(models.StarsFile.objects.count(), 1)
        self.assertIsNotNone(models.Race.objects.get().racefile)

    def test_game_does_not_exist(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        upload_url = reverse('race_update',
                             kwargs={'game_slug': '500-years-after',
                                     'race_slug': 'gestalti'})

        response = self.client.get(upload_url)
        self.assertEqual(response.status_code, 404)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(upload_url, {'file': f})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

    def test_race_does_not_exist(self):
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)

        upload_url = reverse('race_update',
                             kwargs={'game_slug': 'total-war-in-ulfland',
                                     'race_slug': 'histalti'})

        response = self.client.get(upload_url)
        self.assertEqual(response.status_code, 404)

        with open(os.path.join(PATH, 'files', 'gestalti.r1')) as f:
            response = self.client.post(upload_url, {'file': f})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(models.StarsFile.objects.count(), 0)
        self.assertIsNone(self.race.racefile)


class StateFileDownloadTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin',
                                             password='password')
        self.client.login(username='admin', password='password')

        self.game = models.Game(
            name="Total War in Ulfland",
            slug="total-war-in-ulfland",
            host=self.user, state='A',
            description="This *game* is foobared.",
        )
        self.game.save()
        self.race = models.Race(game=self.game,
                                name='Gestalti',
                                plural_name='Gestalti',
                                slug='gestalti',
                                player_number=0)
        self.race.save()
        self.ambassador = models.Ambassador(race=self.race,
                                            user=self.user,
                                            name="KonTiki")
        self.ambassador.save()

        self.starsfile = models.StarsFile(
            type='m', file=SimpleUploadedFile(".m", "turn 2400"))
        self.starsfile.save()

        self.turn = self.game.turns.create(year=2400)
        self.raceturn = self.turn.raceturns.create(race=self.race,
                                                   mfile=self.starsfile)

        self.download_url = reverse('state_download',
                                    kwargs={'game_slug': 'total-war-in-ulfland',
                                            'race_slug': 'gestalti'})

    def tearDown(self):
        for starsfile in models.StarsFile.objects.all():
            starsfile.file.delete()

    def test_authorized(self):
        self.assertEqual(models.StarsFile.objects.filter(type='m').count(), 1)

        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="total-wa.m1"')
        self.assertEqual(response['Content-length'], '9')

    def test_unauthorized(self):
        user = User.objects.create_user(username='jrb', password='password')
        self.client.login(username='jrb', password='password')

        self.assertEqual(models.StarsFile.objects.filter(type='m').count(), 1)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response,
                            "Not authorized to download files for this race.",
                            status_code=403)

    def test_ambassador_no_longer_active(self):
        # Allow players who are no longer active in a game to still
        # download the state file.
        self.ambassador.active = False
        self.ambassador.save()

        self.assertEqual(models.StarsFile.objects.filter(type='m').count(), 1)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'],
                         'attachment; filename="total-wa.m1"')
        self.assertEqual(response['Content-length'], '9')

    def test_anonymous(self):
        self.client.logout()

        self.assertEqual(models.StarsFile.objects.filter(type='m').count(), 1)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response,
                             "{0}?next={1}".format(settings.LOGIN_URL,
                                                   self.download_url))

    def test_game_does_not_exist(self):
        self.assertEqual(models.StarsFile.objects.filter(type='m').count(), 1)

        download_url = reverse('race_download',
                               kwargs={'game_slug': '500-years-after',
                                       'race_slug': 'gestalti'})

        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 404)

    def test_race_does_not_exist(self):
        self.assertEqual(models.StarsFile.objects.filter(type='m').count(), 1)

        download_url = reverse('race_download',
                               kwargs={'game_slug': 'total-war-in-ulfland',
                                       'race_slug': 'histalti'})

        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 404)

    def test_no_turns_have_been_generated(self):
        self.raceturn.delete()

        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 404)
