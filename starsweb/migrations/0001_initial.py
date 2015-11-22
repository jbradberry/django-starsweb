# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import starsweb.models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ambassador',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('description_html', models.TextField(blank=True)),
                ('markup_type', models.CharField(default=b'restructuredtext', max_length=32, choices=[(b'textile', b'textile'), (b'restructuredtext', b'restructuredtext'), (b'markdown', b'markdown')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(default=b'S', max_length=1, choices=[(b'S', b'Setup'), (b'A', b'Active'), (b'P', b'Paused'), (b'F', b'Finished')])),
                ('published', models.BooleanField(default=True)),
                ('host', models.ForeignKey(related_name='starsweb_games', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GameOptions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('universe_size', models.PositiveSmallIntegerField(default=1, choices=[(0, b'Tiny'), (1, b'Small'), (2, b'Medium'), (3, b'Large'), (4, b'Huge')])),
                ('universe_density', models.PositiveSmallIntegerField(default=1, choices=[(0, b'Sparse'), (1, b'Normal'), (2, b'Dense'), (3, b'Packed')])),
                ('starting_distance', models.PositiveSmallIntegerField(default=1, choices=[(0, b'Close'), (1, b'Moderate'), (2, b'Farther'), (3, b'Distant')])),
                ('maximum_minerals', models.BooleanField(default=False, help_text=b'All planets start with a mineral concentration of 100. Not recommended for experienced players.')),
                ('slow_tech', models.BooleanField(default=False, help_text=b'Research will be twice as expensive.')),
                ('accelerated_bbs', models.BooleanField(default=False, help_text=b'Players start with 4 times the normal population, and planets have 20% more minerals.')),
                ('random_events', models.BooleanField(default=True, help_text=b'Allow random occurrences such as Mystery Traders, comets, and wormholes.')),
                ('computer_alliances', models.BooleanField(default=False, help_text=b'Computer players will prefer to attack human players instead of each other.')),
                ('public_scores', models.BooleanField(default=True, help_text=b"All player's scores will be displayed in the score sheet after the first 20 turns.")),
                ('galaxy_clumping', models.BooleanField(default=False, help_text=b'Causes star systems to clump together.')),
                ('ai_players', models.CommaSeparatedIntegerField(max_length=64, blank=True)),
                ('percent_planets', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(20), django.core.validators.MaxValueValidator(100)])),
                ('tech_level', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(8), django.core.validators.MaxValueValidator(26)])),
                ('tech_fields', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(2), django.core.validators.MaxValueValidator(6)])),
                ('score', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1000), django.core.validators.MaxValueValidator(20000)])),
                ('exceeds_nearest_score', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(20), django.core.validators.MaxValueValidator(300)])),
                ('production', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(500)])),
                ('capital_ships', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(10), django.core.validators.MaxValueValidator(300)])),
                ('highest_score_after_years', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(30), django.core.validators.MaxValueValidator(900)])),
                ('num_criteria', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(7)])),
                ('min_turns_to_win', models.IntegerField(default=50, validators=[django.core.validators.MinValueValidator(30), django.core.validators.MaxValueValidator(500)])),
                ('file_contents', models.TextField(blank=True)),
                ('game', models.OneToOneField(related_name='options', to='starsweb.Game')),
            ],
        ),
        migrations.CreateModel(
            name='Race',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=15)),
                ('plural_name', models.CharField(max_length=15)),
                ('slug', models.SlugField(max_length=16)),
                ('player_number', models.PositiveSmallIntegerField(null=True, blank=True)),
                ('is_ai', models.BooleanField(default=False)),
                ('game', models.ForeignKey(related_name='races', to='starsweb.Game')),
            ],
        ),
        migrations.CreateModel(
            name='RacePage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(max_length=32)),
                ('title', models.CharField(max_length=32)),
                ('body', models.TextField()),
                ('body_html', models.TextField()),
                ('markup_type', models.CharField(default=b'restructuredtext', max_length=32, choices=[(b'textile', b'textile'), (b'restructuredtext', b'restructuredtext'), (b'markdown', b'markdown')])),
                ('race', models.ForeignKey(related_name='racepages', to='starsweb.Race')),
            ],
        ),
        migrations.CreateModel(
            name='RaceTurn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uploads', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('section', models.IntegerField(default=0, choices=[(0, b'Rank'), (1, b'Score'), (2, b'Resources'), (3, b'Tech Levels'), (4, b'Capital Ships'), (5, b'Escort Ships'), (6, b'Unarmed Ships'), (7, b'Starbases'), (8, b'Planets')])),
                ('value', models.IntegerField()),
                ('race', models.ForeignKey(related_name='scores', to='starsweb.Race')),
            ],
            options={
                'ordering': ('-turn', 'race'),
            },
        ),
        migrations.CreateModel(
            name='Star',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=18)),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('game', models.ForeignKey(to='starsweb.Game')),
            ],
        ),
        migrations.CreateModel(
            name='StarsFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('type', models.CharField(max_length=3, choices=[(b'r', b'race'), (b'xy', b'map'), (b'm', b'state'), (b'x', b'orders'), (b'h', b'history'), (b'hst', b'host')])),
                ('file', models.FileField(upload_to=starsweb.models.starsfile_path)),
                ('upload_user', models.ForeignKey(related_name='starsweb_files', to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Turn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.IntegerField()),
                ('generated', models.DateTimeField(auto_now_add=True)),
                ('game', models.ForeignKey(related_name='turns', to='starsweb.Game')),
                ('hstfile', models.ForeignKey(related_name='hstturn', to='starsweb.StarsFile', null=True)),
            ],
            options={
                'ordering': ('-generated',),
                'get_latest_by': 'generated',
            },
        ),
        migrations.CreateModel(
            name='UserRace',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=64)),
                ('racefile', models.ForeignKey(blank=True, to='starsweb.StarsFile', null=True)),
                ('user', models.ForeignKey(related_name='starsweb_racepool', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='score',
            name='turn',
            field=models.ForeignKey(related_name='scores', to='starsweb.Turn'),
        ),
        migrations.AddField(
            model_name='raceturn',
            name='hfile',
            field=models.ForeignKey(related_name='hraceturn', to='starsweb.StarsFile', null=True),
        ),
        migrations.AddField(
            model_name='raceturn',
            name='mfile',
            field=models.ForeignKey(related_name='mraceturn', to='starsweb.StarsFile'),
        ),
        migrations.AddField(
            model_name='raceturn',
            name='race',
            field=models.ForeignKey(related_name='raceturns', to='starsweb.Race'),
        ),
        migrations.AddField(
            model_name='raceturn',
            name='turn',
            field=models.ForeignKey(related_name='raceturns', to='starsweb.Turn'),
        ),
        migrations.AddField(
            model_name='raceturn',
            name='xfile',
            field=models.ForeignKey(related_name='xraceturn', to='starsweb.StarsFile', null=True),
        ),
        migrations.AddField(
            model_name='raceturn',
            name='xfile_official',
            field=models.ForeignKey(related_name='official_xraceturn', to='starsweb.StarsFile', null=True),
        ),
        migrations.AddField(
            model_name='race',
            name='homepage',
            field=models.ForeignKey(related_name='+', to='starsweb.RacePage', null=True),
        ),
        migrations.AddField(
            model_name='race',
            name='official_racefile',
            field=models.ForeignKey(related_name='official_race', blank=True, to='starsweb.StarsFile', null=True),
        ),
        migrations.AddField(
            model_name='race',
            name='racefile',
            field=models.ForeignKey(related_name='race', blank=True, to='starsweb.StarsFile', null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='mapfile',
            field=models.ForeignKey(to='starsweb.StarsFile', null=True),
        ),
        migrations.AddField(
            model_name='ambassador',
            name='race',
            field=models.ForeignKey(related_name='ambassadors', to='starsweb.Race'),
        ),
        migrations.AddField(
            model_name='ambassador',
            name='user',
            field=models.ForeignKey(related_name='starsweb_ambassadors', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='userrace',
            unique_together=set([('user', 'identifier')]),
        ),
        migrations.AlterUniqueTogether(
            name='score',
            unique_together=set([('turn', 'race', 'section')]),
        ),
        migrations.AlterUniqueTogether(
            name='race',
            unique_together=set([('game', 'slug'), ('game', 'plural_name'), ('game', 'name'), ('game', 'player_number')]),
        ),
        migrations.AlterUniqueTogether(
            name='ambassador',
            unique_together=set([('race', 'user')]),
        ),
    ]
