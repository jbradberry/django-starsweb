from django.db import models
from django.conf import settings
from operator import attrgetter
from template_utils.markup import formatter


FORMATTERS = tuple((f, f) for f in formatter._filters.iterkeys())
MARKUP_FILTER_OPTS = getattr(settings, 'MARKUP_FILTER_OPTS', {})


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
    markup_type = models.CharField(max_length=32, choices=FORMATTERS)

    hosts = models.ManyToManyField("auth.User", related_name="stars_games")
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default='S')
    published = models.BooleanField()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.description_html = formatter(
            self.description, filter_name=self.markup_type,
            **MARKUP_FILTER_OPTS.get(self.markup_type, {}))
        super(Game, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('starsweb.views.game_detail', (), {'slug': self.slug})

    @property
    def current_turn(self):
        if self.turn_set.exists():
            return self.turn_set.latest()

    @property
    def races(self):
        scores = {}
        if self.current_turn:
            scores = dict(
                self.current_turn.scores.filter(
                    section=Score.SCORE).values_list('race__id', 'value'))
        races = list(self.race_set.all())
        for race in races:
            race.score = scores.get(race.id, None)
        return sorted(races, key=attrgetter('score'), reverse=True)


class Race(models.Model):
    game = models.ForeignKey(Game)
    name = models.CharField(max_length=15)
    plural_name = models.CharField(max_length=15)
    slug = models.SlugField(max_length=16)
    player_number = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (('game', 'slug'),
                           ('game', 'player_number'))

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('starsweb.views.race_detail', (), {'gameslug': self.game.slug,
                                                   'slug': self.slug})

    @property
    def current_ambassador(self):
        if self.ambassador_set.exists():
            return self.ambassador_set.get(active=True)


class Ambassador(models.Model):
    race = models.ForeignKey(Race)
    user = models.ForeignKey("auth.User")
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Turn(models.Model):
    game = models.ForeignKey(Game)
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
