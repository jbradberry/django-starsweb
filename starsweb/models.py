from collections import defaultdict
import glob
import logging
import os.path
import shutil
import tempfile
import uuid

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator, validate_comma_separated_integer_list
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse

from starslib import base

from . import markup, processing

logger = logging.getLogger(__name__)


def starsfile_path(instance, filename):
    return '{type}/{year}/{month}/{day}/{uuid}'.format(
        type=instance.get_type_display(),
        year=instance.timestamp.year,
        month=instance.timestamp.month,
        day=instance.timestamp.day,
        uuid=uuid.uuid4()
    )


class StarsFileType(models.TextChoices):
    RACE = 'r', "race"
    MAP = 'xy', "map"
    STATE = 'm', "state"
    ORDERS = 'x', "orders"
    HISTORY = 'h', "history"
    HOST = 'hst', "host"


class GameState(models.TextChoices):
    SETUP = 'S', "Setup"
    ACTIVE = 'A', "Active"
    PAUSED = 'P', "Paused"
    FINISHED = 'F', "Finished"


class UniverseSize(models.IntegerChoices):
    TINY = 0, "Tiny"
    SMALL = 1, "Small"
    MEDIUM = 2, "Medium"
    LARGE = 3, "Large"
    HUGE = 4, "Huge"


class UniverseDensity(models.IntegerChoices):
    SPARSE = 0, "Sparse"
    NORMAL = 1, "Normal"
    DENSE = 2, "Dense"
    PACKED = 3, "Packed"


class StartingDistance(models.IntegerChoices):
    CLOSE = 0, "Close"
    MODERATE = 1, "Moderate"
    FARTHER = 2, "Farther"
    DISTANT = 3, "Distant"


class AIRace(models.IntegerChoices):
    RANDOM = 0, "Random"
    ROBOTOIDS = 1, "Robotoids"
    TURINDRONES = 2, "Turindrones"
    AUTOMITRONS = 3, "Automitrons"
    ROTOTILLS = 4, "Rototills"
    CYBERTRONS = 5, "Cybertrons"
    MACINTI = 6, "Macinti"

    __empty__ = "-------"


class AISkillLevel(models.IntegerChoices):
    RANDOM = 0, "Random"
    EASY = 1, "Easy"
    STANDARD = 2, "Standard"
    TOUGH = 3, "Tough"
    EXPERT = 4, "Expert"

    __empty__ = "-------"


class ScoreSection(models.IntegerChoices):
    RANK = 0, "Rank"  # The Struct45.year field is the player rank in .m* files.
    SCORE = 1, "Score"
    RESOURCES = 2, "Resources"
    TECHLEVELS = 3, "Tech Levels"
    CAPSHIPS = 4, "Capital Ships"
    ESCORTSHIPS = 5, "Escort Ships"
    UNARMEDSHIPS = 6, "Unarmed Ships"
    STARBASES = 7, "Starbases"
    PLANETS = 8, "Planets"


class StarsFile(models.Model):
    upload_user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True,
                                    related_name='starsweb_files')
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=3, choices=StarsFileType.choices)
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
    def from_file(cls, _file, type=None, **kwargs):
        try:  # FIXME
            _file.open('rb')
            data = _file.read()
        finally:
            _file.close()

        return cls.from_data(data, type, **kwargs)

    @staticmethod
    def parse(data, type=None):
        sfile = base.StarsFile()
        sfile.bytes = data

        if type is not None and sfile.type != type:
            raise ValueError(f"Expected StarsFile type {type}, received {sfile.type}.")

        return sfile


class Game(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    description = models.TextField(blank=True)
    description_html = models.TextField(blank=True)

    host = models.ForeignKey("auth.User", on_delete=models.SET(1), related_name='starsweb_games')
    created = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=1, choices=GameState.choices, default=GameState.SETUP)
    published = models.BooleanField(default=True)

    mapfile = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.description_html = markup.process(self.description)
        super(Game, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('game_detail', kwargs={'slug': self.slug})

    @property
    def current_turn(self):
        if self.turns.exists():
            return self.turns.latest()

    def _tempdir_create(self):
        # Create a temporary directory for Stars to work in.
        path = tempfile.mkdtemp()
        winpath = r'Z:{}\\'.format(path.replace('/', r'\\'))

        logger.info(f"Created temp directory for '{self.name}' (pk={self.pk}): {path}")
        return path, winpath

    def _tempdir_remove(self, path):
        # Delete the temp directory.
        shutil.rmtree(path)
        logger.info(f"Deleted temp directory for '{self.name}' (pk={self.pk}): {path}")

    def generate(self):
        path, winpath = self._tempdir_create()

        if self.state == GameState.SETUP:
            self._activate(path, winpath)
        elif self.state in (GameState.ACTIVE, GameState.PAUSED):
            self._generate(path, winpath)
        else:
            logger.error(
                f"Game generation attempted on inactive game '{self.name}' (pk={self.pk}, state={self.state})."
            )

        self._tempdir_remove(path)

    def _activate(self, path, winpath):
        # Move the game into active state.
        self.state = GameState.ACTIVE
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
            filename = f'race.r{race.player_number + 1}'
            with open(os.path.join(path, filename), 'wb') as f:
                f.write(new_starsfile._data)

            race.save()

        # Render the game options and write to a .def file.
        opts = self.options.render(winpath)
        self.options.file_contents = opts
        self.options.save()
        with open(os.path.join(path, 'game.def'), 'w') as f:
            f.write(opts)

        # Call out to Stars to create the new game files.
        logger.info(f"Generating start files for '{self.name}' (pk={self.pk}).")

        processing.activate(winpath)

        host = self._process_host(path)
        self._process_activation(path, host)

    def _generate(self, path, winpath):
        current = self.current_turn

        # Write out the host file to the temp directory.
        try:  # FIXME
            current.hstfile.file.open('rb')
            hst = current.hstfile.file.read()
        finally:
            current.hstfile.file.close()

        with open(os.path.join(path, 'game.hst'), 'wb') as f:
            f.write(hst)

        # Write out the map file.
        try:  # FIXME
            self.mapfile.file.open('rb')
            xyfile = self.mapfile.file.read()
        finally:
            self.mapfile.file.close()

        with open(os.path.join(path, 'game.xy'), 'wb') as f:
            f.write(xyfile)

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
                    path, f'game.x{raceturn.race.player_number + 1}')
                with open(target, 'wb') as f:
                    f.write(raceturn.xfile_official._data)

        # Call out to Stars to generate the new turn files.
        processing.generate(winpath)

        host = self._process_host(path)
        self._process_generation(path, host)

    def _process_host(self, path):
        # Fetch the host file and parse it.
        hst_files = glob.glob(f'{path}/*.hst')
        if len(hst_files) != 1:
            raise Exception(
                f"Expected one hst file, found {len(hst_files)}.")

        with open(hst_files[0], 'rb') as f:
            hst = StarsFile.from_data(f.read())

        return hst

    def _process_activation(self, path, host):
        # Process and attach the game.xy map file.
        xy_files = glob.glob(f'{path}/*.xy')
        if len(xy_files) != 1:
            raise Exception(
                f"Expected one xy file, found {len(xy_files)}.")

        with open(xy_files[0], 'rb') as f:
            self.mapfile = StarsFile.from_data(f.read())
        self.save()

        # Check the resultant races for any that need to be created or changed.
        races = {r.player_number: r for r in self.races.filter(player_number__isnull=False)}

        for r in host._sfile.structs:
            if r.type != 6:  # Type 6 is the Race data structure.
                continue

            race_obj = races.get(r.player)

            # Grab the name and plural name out of the race struct.
            name, plural_name = r.race_name, r.plural_race_name
            if not plural_name:
                plural_name = f'{name}s'

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

        self._process_generation(path, host)

    def _process_generation(self, path, host):
        # Create the new turn with host file attached.
        turn = self.turns.create(year=2400 + host._sfile.structs[0].turn,
                                 hstfile=host)

        # Process the m files.
        races = {r.player_number: r for r in self.races.filter(player_number__isnull=False)}
        scores = defaultdict(set)
        scores_unmatched = {(race, section) for race in races for section in ScoreSection.values}

        STRUCT_FIELDS = {
            'rank': 'year',
            'techlevels': 'tech_levels',
            'capships': 'capital_ships',
            'escortships': 'escort_ships',
            'unarmedships': 'unarmed_ships',
        }

        for m_name in glob.glob(f'{path}/*.m[0-9]*'):
            with open(m_name, 'rb') as f:
                mfile = StarsFile.from_data(f.read())

            structs = mfile._sfile.structs
            player = structs[0].player

            # Create a new Race-Turn intermediate table entry, with
            # the m file attached.
            turn.raceturns.create(race=races[player], mfile=mfile)

            for S in structs:
                if S.type != 45:  # Type 45 is the Score data structure.
                    continue

                for sname in ScoreSection.names:
                    sfield, section = sname.lower(), ScoreSection[sname]
                    sfield = STRUCT_FIELDS.get(sfield, sfield)
                    value = getattr(S, sfield, 0)

                    # Save all scores from this file, to potentially
                    # fill in any blanks in the record.
                    scores[(S.player, section)].add(value)

                    # A player's own score record is canonical, so use
                    # that if available.
                    if S.player == player:
                        turn.scores.create(race=races[player], section=section, value=value)
                        scores_unmatched.remove((S.player, section))

        # If there are any blank scores left over, fill them in with
        # data from the other m files.
        if scores_unmatched and scores:
            logger.info(
                "Filling in blanks for players, game id: {}, players: ({})".format(
                    self.id,
                    ', '.join(str(player)
                              for player, section in scores_unmatched)
                )
            )

            for player, section in scores_unmatched:
                if len(scores[(player, section)]) > 1:
                    logger.info(
                        f"More than one distinct score found, game id: {self.id}, player: {player}, section: {section}"
                    )

                turn.scores.create(
                    race=races[player], section=section,
                    value=max(scores[(player, section)])
                )


class GameOptions(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name='options')

    universe_size = models.PositiveSmallIntegerField(choices=UniverseSize.choices, default=UniverseSize.SMALL)
    universe_density = models.PositiveSmallIntegerField(choices=UniverseDensity.choices, default=UniverseDensity.NORMAL)
    starting_distance = models.PositiveSmallIntegerField(choices=StartingDistance.choices, default=StartingDistance.MODERATE)

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

    ai_players = models.CharField(max_length=64, blank=True, validators=[validate_comma_separated_integer_list])

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
        return f"1 {option}"

    def render(self, path):
        random_events = not self.random_events
        boolean_opts = (
            f"{self.maximum_minerals:d} {self.slow_tech:d} {self.accelerated_bbs:d} {random_events:d}"
            f" {self.computer_alliances:d} {self.public_scores:d} {self.galaxy_clumping:d}"
        )

        races = self.game.races.filter(player_number__isnull=False).order_by('player_number')
        players = [f"{path}race.r{race.player_number + 1}" for race in races]
        players.extend(
            "# {} {}".format(*ai)
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
           vc_tech_levels=0 if self.tech_level is None else f"1 {self.tech_level} {self.tech_fields}",
           vc_score=self.opt_format(self.score),
           vc_pct_exceeds=self.opt_format(self.exceeds_nearest_score),
           vc_production=self.opt_format(self.production),
           vc_capships=self.opt_format(self.capital_ships),
           vc_highest_score_after=self.opt_format(self.highest_score_after_years),
           file_path=f"{path}{self.game.slug[:8]}.xy")

        return contents


class Race(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='races')
    name = models.CharField(max_length=15)
    plural_name = models.CharField(max_length=15)
    slug = models.SlugField(max_length=16)
    player_number = models.PositiveSmallIntegerField(null=True, blank=True)
    is_ai = models.BooleanField(default=False)
    racefile = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='race')
    official_racefile = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='official_race')
    homepage = models.ForeignKey('RacePage', on_delete=models.SET_NULL, null=True, related_name='+')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('game', 'slug'), name='race_slug_per_game'),
            models.UniqueConstraint(fields=('game', 'name'), name='race_name_per_game'),
            models.UniqueConstraint(fields=('game', 'plural_name'), name='race_plural_name_per_game'),
            models.UniqueConstraint(fields=('game', 'player_number'), name='race_player_number_per_game'),
        ]

    def __str__(self):
        return self.plural_name

    def get_absolute_url(self):
        return reverse('race_detail',
                       kwargs={'game_slug': self.game.slug, 'slug': self.slug})

    @property
    def all_ambassadors(self):
        if self.ambassadors.exists():
            return ' / '.join(str(a) for a in self.ambassadors.all())

    @property
    def number(self):
        if self.player_number is not None:
            return self.player_number + 1


class RacePage(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='racepages')
    slug = models.SlugField(max_length=32)
    title = models.CharField(max_length=32)
    body = models.TextField()
    body_html = models.TextField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.body_html = markup.process(self.body)

        max_length = self._meta.get_field('slug').max_length
        slug, num, end = slugify(self.title), 1, ''
        if len(slug) > max_length:
            slug = slug[:max_length]

        while self.race.racepages.filter(slug=slug+end).exists():
            num += 1
            end = f"-{num}"
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
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='starsweb_racepool')
    identifier = models.CharField(max_length=64)
    racefile = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'identifier'), name='userrace_identifier_per_user')]

    def __str__(self):
        return self.identifier


class Ambassador(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='ambassadors')
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name='starsweb_ambassadors')
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('race', 'user'), name='ambassador_user_per_race')]

    def __str__(self):
        return self.name


class Turn(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='turns')
    year = models.IntegerField()
    generated = models.DateTimeField(auto_now_add=True)
    hstfile = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True, related_name='hstturn')

    class Meta:
        get_latest_by = 'generated'
        ordering = ('-generated',)

    def __str__(self):
        return str(self.year)


class RaceTurn(models.Model):
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='raceturns')
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE, related_name='raceturns')
    mfile = models.ForeignKey(StarsFile, on_delete=models.CASCADE, related_name='mraceturn')
    hfile = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True, related_name='hraceturn')
    xfile = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True, related_name='xraceturn')
    xfile_official = models.ForeignKey(StarsFile, on_delete=models.SET_NULL, null=True,
                                       related_name='official_xraceturn')
    uploads = models.IntegerField(default=0)


class Score(models.Model):
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE, related_name='scores')
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='scores')
    section = models.IntegerField(choices=ScoreSection.choices, default=ScoreSection.RANK)
    value = models.IntegerField()

    class Meta:
        ordering = ('-turn', 'race')
        constraints = [models.UniqueConstraint(fields=('turn', 'race', 'section'), name='score_datapoint')]

    def __str__(self):
        return f"{self.get_section_display()}: {self.value}"


class Star(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=18)
    x = models.IntegerField()
    y = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.x}, {self.y})"
