from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from operator import attrgetter
import uuid

from . import markup


class Game(models.Model):
    STATE_CHOICES = (
        ('S', 'Setup'),
        ('A', 'Active'),
        ('P', 'Paused'),
        ('F', 'Finished')
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True)
    description_html = models.TextField(blank=True)
    markup_type = models.CharField(max_length=32, choices=markup.FORMATTERS,
                                   default=markup.DEFAULT_MARKUP)

    host = models.ForeignKey("auth.User", related_name='stars_games')
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    published = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.description_html = markup.process(self.description,
                                               self.markup_type)
        super(Game, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('game_detail', kwargs={'slug': self.slug})

    @property
    def press(self):
        if 'micropress' in settings.INSTALLED_APPS:
            press = models.get_model('micropress', 'press')
            ct = ContentType.objects.get(app_label="starsweb",
                                         model="game")
            press = press.objects.filter(
                content_type=ct,
                object_id=self.id)
            if press.exists():
                return press.get()

    @property
    def current_turn(self):
        if self.turns.exists():
            return self.turns.latest()


def racefile_path(instance, filename):
    return 'race/{user}/{uuid}.r1'.format(user=instance.user_id,
                                          uuid=uuid.uuid4())


class RaceFile(models.Model):
    user = models.ForeignKey('auth.User', related_name='racefiles')
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=15)
    plural_name = models.CharField(max_length=15)
    file = models.FileField(upload_to=racefile_path)


class Race(models.Model):
    game = models.ForeignKey(Game, related_name='races')
    name = models.CharField(max_length=15)
    plural_name = models.CharField(max_length=15)
    slug = models.SlugField(max_length=16)
    player_number = models.PositiveSmallIntegerField(null=True, blank=True)
    racefile = models.ForeignKey(RaceFile, null=True)

    class Meta:
        unique_together = (('game', 'slug'),
                           ('game', 'name'),
                           ('game', 'plural_name'),
                           ('game', 'player_number'))

    def __unicode__(self):
        return self.plural_name

    def get_absolute_url(self):
        return reverse('race_detail',
                       kwargs={'game_slug': self.game.slug, 'slug': self.slug})

    @property
    def all_ambassadors(self):
        if self.ambassadors.exists():
            return u' / '.join(unicode(a) for a in self.ambassadors.all())

    @property
    def number(self):
        if self.player_number is not None:
            return self.player_number + 1


class Ambassador(models.Model):
    race = models.ForeignKey(Race, related_name='ambassadors')
    user = models.ForeignKey("auth.User")
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('race', 'user')

    def __unicode__(self):
        return self.name


class GameRaceFile(models.Model):
    race = models.ForeignKey(Race, unique=True)
    racefile = models.ForeignKey(RaceFile)


class Turn(models.Model):
    game = models.ForeignKey(Game, related_name='turns')
    year = models.IntegerField()
    generated = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = 'generated'
        ordering = ('-generated',)

    def __unicode__(self):
        return unicode(self.year)


class Score(models.Model):
    RANK = 0
    SCORE = 1
    RESOURCES = 2
    TECHLEVELS = 3
    CAPSHIPS = 4
    ESCORTSHIPS = 5
    UNARMEDSHIPS = 6
    STARBASES = 7
    PLANETS = 8

    SECTIONS = ((RANK, 'Rank'),
                (SCORE, 'Score'),
                (RESOURCES, 'Resources'),
                (TECHLEVELS, 'Tech Levels'),
                (CAPSHIPS, 'Capital Ships'),
                (ESCORTSHIPS, 'Escort Ships'),
                (UNARMEDSHIPS, 'Unarmed Ships'),
                (STARBASES, 'Starbases'),
                (PLANETS, 'Planets'),)

    turn = models.ForeignKey(Turn, related_name='scores')
    race = models.ForeignKey(Race, related_name='scores')
    section = models.IntegerField(choices=SECTIONS, default=RANK)
    value = models.IntegerField()

    class Meta:
        ordering = ('-turn', 'race')
        unique_together = ('turn', 'race', 'section')

    def __unicode__(self):
        return u"{0}: {1}".format(self.get_section_display(), self.value)
