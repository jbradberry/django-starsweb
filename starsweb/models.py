from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models
from operator import attrgetter
import uuid
import logging
from starslib import base

from . import markup

logger = logging.getLogger(__name__)


def starsfile_path(instance, filename):
    return '{type}/{year}/{month}/{day}/{uuid}'.format(
        type=instance.get_type_display(),
        year=instance.timestamp.year,
        month=instance.timestamp.month,
        day=instance.timestamp.day,
        uuid=uuid.uuid4()
    )


class StarsFile(models.Model):
    STARS_TYPES = (('r', 'race'),
                   ('xy', 'map'),
                   ('m', 'state'),
                   ('x', 'orders'),
                   ('h', 'history'),
                   ('hst', 'host'))

    upload_user = models.ForeignKey('auth.User', null=True,
                                    related_name='starsfiles')
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=3, choices=STARS_TYPES)
    file = models.FileField(upload_to=starsfile_path)

    @classmethod
    def from_data(cls, data, type=None, **kwargs):
        sfile = cls.parse(data, type)

        starsfile = StarsFile.objects.create(type=sfile.type, **kwargs)
        starsfile.file.save(sfile.type, ContentFile(data))
        starsfile._sfile = sfile
        starsfile._data = data

        return starsfile

    @classmethod
    def from_file(cls, file, type=None, **kwargs):
        try:
            file.open()
            data = file.read()
        finally:
            file.close()

        return cls.from_data(data, type, **kwargs)

    @staticmethod
    def parse(data, type=None):
        sfile = base.StarsFile()
        sfile.bytes = data

        if type is not None and sfile.type != type:
            raise ValueError("Expected StarsFile type {0},"
                             " received {1}.".format(type, sfile.type))

        return sfile


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

    mapfile = models.ForeignKey(StarsFile, null=True)

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


class GameOptions(models.Model):
    SIZE_CHOICES = ((0, 'Tiny'),
                    (1, 'Small'),
                    (2, 'Medium'),
                    (3, 'Large'),
                    (4, 'Huge'))

    DENSITY_CHOICES = ((0, 'Sparse'),
                       (1, 'Normal'),
                       (2, 'Dense'),
                       (3, 'Packed'))

    DISTANCE_CHOICES = ((0, 'Close'),
                        (1, 'Moderate'),
                        (2, 'Farther'),
                        (3, 'Distant'))

    AI_RACES = ((0, 'Random'),
                (1, 'Robotoids'),
                (2, 'Turindrones'),
                (3, 'Automitrons'),
                (4, 'Rototills'),
                (5, 'Cybertrons'),
                (6, 'Macinti'))

    AI_SKILL_LEVELS = ((0, 'Random'),
                       (1, 'Easy'),
                       (2, 'Standard'),
                       (3, 'Tough'),
                       (4, 'Expert'))

    game = models.OneToOneField(Game, related_name='options')

    universe_size = models.PositiveSmallIntegerField(
        choices=SIZE_CHOICES, default=1)
    universe_density = models.PositiveSmallIntegerField(
        choices=DENSITY_CHOICES, default=1)
    starting_distance = models.PositiveSmallIntegerField(
        choices=DISTANCE_CHOICES, default=1)

    maximum_minerals = models.BooleanField(
        default=False, blank=True,
        help_text="All planets start with a mineral concentration of 100."
        " Not recommended for experienced players."
    )
    slow_tech = models.BooleanField(
        default=False, blank=True,
        help_text="Research will be twice as expensive."
    )
    accelerated_bbs = models.BooleanField(
        default=False, blank=True,
        help_text="Players start with 4 times the normal population,"
        " and planets have 20% more minerals."
    )
    random_events = models.BooleanField(
        default=True, blank=True,
        help_text="Allow random occurrences such as Mystery Traders,"
        " comets, and wormholes."
    )
    computer_alliances = models.BooleanField(
        default=False, blank=True,
        help_text="Computer players will prefer to attack human players"
        " instead of each other."
    )
    public_scores = models.BooleanField(
        default=True, blank=True,
        help_text="All player's scores will be displayed in the score"
        " sheet after the first 20 turns."
    )
    galaxy_clumping = models.BooleanField(
        default=False, blank=True,
        help_text="Causes star systems to clump together."
    )

    ai_players = models.CommaSeparatedIntegerField(max_length=64, blank=True)

    percent_planets = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(100)])

    tech_level = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(8), MaxValueValidator(26)])
    tech_fields = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(2), MaxValueValidator(6)])

    score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1000), MaxValueValidator(20000)])

    exceeds_nearest_score = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)])

    production = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(500)])

    capital_ships = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(300)])

    highest_score_after_years = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(900)])

    num_criteria = models.IntegerField(
        default=1,
        validators=[MinValueValidator(0), MaxValueValidator(7)])

    min_turns_to_win = models.IntegerField(
        default=50,
        validators=[MinValueValidator(30), MaxValueValidator(500)])

    file_contents = models.TextField(blank=True)


class Race(models.Model):
    game = models.ForeignKey(Game, related_name='races')
    name = models.CharField(max_length=15)
    plural_name = models.CharField(max_length=15)
    slug = models.SlugField(max_length=16)
    player_number = models.PositiveSmallIntegerField(null=True, blank=True)
    is_ai = models.BooleanField(default=False)
    racefile = models.ForeignKey(StarsFile, null=True, blank=True,
                                 related_name='race')
    official_racefile = models.ForeignKey(StarsFile, null=True, blank=True,
                                          related_name='official_race')

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


class UserRace(models.Model):
    user = models.ForeignKey('auth.User', related_name='racepool')
    identifier = models.CharField(max_length=64)
    racefile = models.ForeignKey(StarsFile, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'identifier')

    def __unicode__(self):
        return self.identifier


class Ambassador(models.Model):
    race = models.ForeignKey(Race, related_name='ambassadors')
    user = models.ForeignKey("auth.User")
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('race', 'user')

    def __unicode__(self):
        return self.name


class Turn(models.Model):
    game = models.ForeignKey(Game, related_name='turns')
    year = models.IntegerField()
    generated = models.DateTimeField(auto_now_add=True)
    hstfile = models.ForeignKey(StarsFile, null=True, related_name='hstturn')

    class Meta:
        get_latest_by = 'generated'
        ordering = ('-generated',)

    def __unicode__(self):
        return unicode(self.year)


class RaceTurn(models.Model):
    race = models.ForeignKey(Race, related_name='raceturns')
    turn = models.ForeignKey(Turn, related_name='raceturns')
    mfile = models.ForeignKey(StarsFile, related_name='mraceturn')
    hfile = models.ForeignKey(StarsFile, null=True, related_name='hraceturn')
    xfile = models.ForeignKey(StarsFile, null=True, related_name='xraceturn')
    xfile_official = models.ForeignKey(StarsFile, null=True,
                                       related_name='official_xraceturn')
    uploads = models.IntegerField(default=0)


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

    FIELDS = (
        ('year', RANK),
        ('score', SCORE),
        ('resources', RESOURCES),
        ('tech_levels', TECHLEVELS),
        ('capital_ships', CAPSHIPS),
        ('escort_ships', ESCORTSHIPS),
        ('unarmed_ships', UNARMEDSHIPS),
        ('starbases', STARBASES),
        ('planets', PLANETS),
    )

    TOKENS = ('rank', 'score', 'resources', 'techlevels', 'capships',
              'escortships', 'unarmedships', 'starbases', 'planets')

    NAMES = tuple(
        (token, name)
        for token, (value, name) in zip(TOKENS, SECTIONS)
    )

    turn = models.ForeignKey(Turn, related_name='scores')
    race = models.ForeignKey(Race, related_name='scores')
    section = models.IntegerField(choices=SECTIONS, default=RANK)
    value = models.IntegerField()

    class Meta:
        ordering = ('-turn', 'race')
        unique_together = ('turn', 'race', 'section')

    def __unicode__(self):
        return u"{0}: {1}".format(self.get_section_display(), self.value)
