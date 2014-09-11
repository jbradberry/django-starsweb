from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models

from operator import attrgetter
import subprocess
import logging
import os.path
import uuid
import glob

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
                                    related_name='starsweb_files')
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

    host = models.ForeignKey("auth.User", related_name='starsweb_games')
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
    def current_turn(self):
        if self.turns.exists():
            return self.turns.latest()

    def activate(self, path):
        # Move the game into active state.
        if self.state != 'S':
            logger.error(
                "Game activation attempted on game not in setup"
                " '{game.name}' (pk={game.pk}).".format(game=self)
            )
            return
        self.state = 'A'
        self.save()

        # Process the race files for each race.
        i = 0
        for race in self.races.all():
            # If the player hasn't uploaded, mark them as inactive by
            # giving them a null player number.
            if race.racefile is None:
                race.player_number = None
                race.save()
                continue

            race.player_number = i
            i += 1

            # Make a copy of their most recent uploaded file as the
            # official copy.
            new_starsfile = StarsFile.from_file(
                race.racefile.file, upload_user=race.racefile.upload_user)
            race.official_racefile = new_starsfile

            # Write out the race file to the temp directory.
            filename = 'race.r{0}'.format(race.player_number + 1)
            with open(os.path.join(path, filename), 'w') as f:
                f.write(new_starsfile._data)

            race.save()

        winpath = r'Z:{0}\\'.format(path.replace('/', r'\\'))

        # Render the game options and write to a .def file.
        opts = self.options.render(winpath)
        self.options.file_contents = opts
        self.options.save()
        with open(os.path.join(path, 'game.def'), 'w') as f:
            f.write(opts)

        # Call out to Stars to create the new game files.
        logger.info("Generating start files for '{game.name}'"
                    " (pk={game.pk}).".format(game=self))

        display = getattr(settings, 'DISPLAY', None)
        display = '' if display is None else "DISPLAY={0} ".format(display)

        subprocess.call(
            r'{display}wine C:\\stars\\stars\!.exe'
            r' -a {winpath}game.def'.format(winpath=winpath, display=display),
            shell=True
        )

        self.process_activation(path)

    def generate(self, path):
        winpath = r'Z:{0}\\'.format(path.replace('/', r'\\'))

        current = self.current_turn

        # Write out the host file to the temp directory.
        try:
            current.hstfile.file.open()
            hst = current.hstfile.file.read()
        finally:
            current.hstfile.file.close()

        with open(os.path.join(path, 'game.hst'), 'w') as f:
            f.write(hst)

        # Process the x files for every race playing.
        for raceturn in current.raceturns.all():
            if raceturn.xfile:
                # Save off the most recent x file as the official one.
                raceturn.xfile_official = StarsFile.from_file(
                    raceturn.xfile.file,
                    upload_user=raceturn.xfile.upload_user
                )
                raceturn.save()

                # Write out the x file to the temp directory.
                target = os.path.join(
                    path, 'game.x{0}'.format(raceturn.race.player_number + 1))
                with open(target, 'w') as f:
                    f.write(raceturn.xfile_official._data)

        display = getattr(settings, 'DISPLAY', None)
        display = '' if display is None else "DISPLAY={0} ".format(display)

        # Call out to Stars to generate the new turn files.
        subprocess.call(
            r'{display}wine C:\\stars\\stars\!.exe'
            r' -g {winpath}game.hst'.format(winpath=winpath, display=display),
            shell=True
        )

        self.process_new_turn(path)

    def process_activation(self, path):
        # Process and attach the game.xy map file.
        xy_files = glob.glob('{0}/*.xy'.format(path))
        if len(xy_files) != 1:
            raise Exception(
                "Expected one xy file, found {0}.".format(len(xy_files)))

        with open(xy_files[0]) as f:
            self.mapfile = StarsFile.from_data(f.read())
        self.save()

        # Process the host file.
        hst_files = glob.glob('{0}/*.hst'.format(path))
        if len(hst_files) != 1:
            raise Exception(
                "Expected one hst file, found {0}.".format(len(hst_files)))

        with open(hst_files[0]) as f:
            hst = StarsFile.from_data(f.read())

        # Check the resultant races for any that need to be created or changed.
        races = dict((r.player_number, r)
                     for r in self.races.filter(player_number__isnull=False))

        for r in hst._sfile.structs:
            if r.type != 6: # Type 6 is the Race data structure.
                continue

            race_obj = races.get(r.player)

            # Grab the name and plural name out of the race struct.
            name, plural_name = r.race_name, r.plural_race_name
            if not plural_name:
                plural_name = '{0}s'.format(name)

            # If the race object doesn't exist yet, it's an AI player,
            # so create it.
            if race_obj is None:
                self.races.create(name=name, plural_name=plural_name,
                                  is_ai=True, player_number=r.player)
                continue

            # Update the player race names if they got bumped due to a conflict.
            if (race_obj.name != name or race_obj.plural_name != plural_name):
                Race.objects.filter(pk=race_obj.pk).update(
                    name=name, plural_name=plural_name)

        self.process_new_turn(path, hst)

    def process_new_turn(self, path, hst=None):
        # Get and process the host file if we didn't already from
        # process_activation.
        if hst is None:
            hst_files = glob.glob('{0}/*.hst'.format(path))
            if len(hst_files) != 1:
                raise Exception(
                    "Expected one hst file, found {0}.".format(len(hst_files)))

            with open(hst_files[0]) as f:
                hst = StarsFile.from_data(f.read())

        # Create the new turn with host file attached.
        turn = self.turns.create(year=2400 + hst._sfile.structs[0].turn,
                                 hstfile=hst)

        # Process the m files.
        races = dict((r.player_number, r)
                     for r in self.races.filter(player_number__isnull=False))
        scores = {}
        scores_unmatched = set((race, section) for race in races
                               for sfield, section in Score.FIELDS)

        for m_name in glob.glob('{0}/*.m[0-9]*'.format(path)):
            with open(m_name) as f:
                mfile = StarsFile.from_data(f.read())

            structs = mfile._sfile.structs
            player = structs[0].player

            # Create a new Race-Turn intermediate table entry, with
            # the m file attached.
            raceturn = turn.raceturns.create(race=races[player], mfile=mfile)

            for S in structs:
                if S.type != 45: # Type 45 is the Score data structure.
                    continue

                for sfield, section in Score.FIELDS:
                    value = getattr(S, sfield, 0)

                    # Save all scores from this file, to potentially
                    # fill in any blanks in the record.
                    scores.setdefault((S.player, section), set()).add(value)

                    # A player's own score record is canonical, so use
                    # that if available.
                    if S.player == player:
                        turn.scores.create(
                            race=races[player], section=section, value=value)
                        scores_unmatched.remove((S.player, section))

        # If there are any blank scores left over, fill them in with
        # data from the other m files.
        if scores_unmatched and scores:
            logger.info(
                "Filling in blanks for players,"
                " game id: {0}, players: ({1})".format(
                    self.id,
                    ', '.join(str(player)
                              for player, section in scores_unmatched)
                )
            )

            for player, section in scores_unmatched:
                if len(scores[(player, section)]) > 1:
                    logger.info(
                        "More than one distinct score found,"
                        " game id: {0}, player: {1}, section: {2}".format(
                            self.id, player, section)
                    )

                turn.scores.create(
                    race=races[player], section=section,
                    value=max(scores[(player, section)])
                )


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

    @staticmethod
    def opt_format(option):
        if option is None:
            return "0"
        return "1 {0}".format(option)

    def render(self, path):
        boolean_opts = ("{self.maximum_minerals:d} {self.slow_tech:d}"
                        " {self.accelerated_bbs:d} {random_events:d}"
                        " {self.computer_alliances:d} {self.public_scores:d}"
                        " {self.galaxy_clumping:d}".format(
                            self=self, random_events=not self.random_events))

        races = self.game.races.filter(player_number__isnull=False
                                       ).order_by('player_number')
        players = [
            "{path}race.r{i}".format(path=path, i=race.player_number + 1)
            for race in races
        ]
        players.extend(
            "# {0} {1}".format(*ai)
            for ai in zip(*[iter(self.ai_players.split(','))]*2)
        )
        del players[16:]

        contents = """\
{self.game.name}
{self.universe_size} {self.universe_density} {self.starting_distance}
{boolean_opts}
{num_players}
{player_desc}
{vc_pct_planets}
{vc_tech_levels}
{vc_score}
{vc_pct_exceeds}
{vc_production}
{vc_capships}
{vc_highest_score_after}
{self.num_criteria} {self.min_turns_to_win}
{file_path}
""".format(self=self, boolean_opts=boolean_opts,
           num_players=len(players),
           player_desc="\n".join(players),
           vc_pct_planets=self.opt_format(self.percent_planets),
           vc_tech_levels=0 if self.tech_level is None else "1 {0} {1}".format(
               self.tech_level, self.tech_fields),
           vc_score=self.opt_format(self.score),
           vc_pct_exceeds=self.opt_format(self.exceeds_nearest_score),
           vc_production=self.opt_format(self.production),
           vc_capships=self.opt_format(self.capital_ships),
           vc_highest_score_after=self.opt_format(self.highest_score_after_years),
           file_path="{0}{1}.xy".format(path, self.game.slug[:8]))

        return contents


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
    homepage = models.ForeignKey('RacePage', null=True, related_name='+')

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


class RacePage(models.Model):
    race = models.ForeignKey(Race, related_name='racepages')
    slug = models.SlugField(max_length=32)
    title = models.CharField(max_length=32)
    body = models.TextField()
    body_html = models.TextField()
    markup_type = models.CharField(max_length=32, choices=markup.FORMATTERS,
                                   default=markup.DEFAULT_MARKUP)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.body_html = markup.process(self.body, self.markup_type)

        max_length = self._meta.get_field('slug').max_length
        slug, num, end = slugify(self.title), 1, ''
        if len(slug) > max_length:
            slug = slug[:max_length]

        while self.race.racepages.filter(slug=slug+end).exists():
            num += 1
            end = "-{0}".format(num)
            if len(slug) + len(end) > max_length:
                slug = slug[:max_length - len(end)]

        self.slug = slug + end

        super(RacePage, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('race_page',
                       kwargs={'game_slug': self.race.game.slug,
                               'race_slug': self.race.slug,
                               'slug': self.slug})


class UserRace(models.Model):
    user = models.ForeignKey('auth.User', related_name='starsweb_racepool')
    identifier = models.CharField(max_length=64)
    racefile = models.ForeignKey(StarsFile, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'identifier')

    def __unicode__(self):
        return self.identifier


class Ambassador(models.Model):
    race = models.ForeignKey(Race, related_name='ambassadors')
    user = models.ForeignKey("auth.User", related_name='starsweb_ambassadors')
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

    TOKEN_VALUES = dict(
        (value, token)
        for token, (value, name) in zip(TOKENS, SECTIONS)
    )

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
