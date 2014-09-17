from django.template.defaultfilters import slugify
from django.db.models import BLANK_CHOICE_DASH
from django.conf import settings
from django import forms

from starslib import base

from . import models


class CreateGameForm(forms.ModelForm):
    class Meta:
        model = models.Game
        exclude = ('description_html', 'markup_type', 'host', 'created',
                   'state', 'mapfile')


class AiPlayersWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        _widgets = [
            forms.Select(attrs=attrs,
                         choices=BLANK_CHOICE_DASH + list(w))
            for x in xrange(16)
            for w in (models.GameOptions.AI_RACES,
                      models.GameOptions.AI_SKILL_LEVELS)
        ]
        return super(AiPlayersWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        new_value = [None for x in xrange(32)]
        if value:
            values = [int(x.strip()) for x in value.split(',')]
            L = len(values) // 2 * 2
            new_value[:L] = values[:L]
        return new_value


class AiPlayers(forms.MultiValueField):
    widget = AiPlayersWidget

    def __init__(self, *args, **kwargs):
        fields = [
            forms.ChoiceField(choices=BLANK_CHOICE_DASH + list(w),
                              required=False)
            for x in xrange(16)
            for w in (models.GameOptions.AI_RACES,
                      models.GameOptions.AI_SKILL_LEVELS)
        ]
        super(AiPlayers, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        values = []
        for race, skill in zip(*[iter(data_list)]*2):
            if race and skill:
                values.extend([race, skill])
        return ','.join(values)


class GameOptionsForm(forms.ModelForm):
    ai_players = AiPlayers(required=False)

    class Meta:
        model = models.GameOptions
        exclude = ('game', 'file_contents')


class RaceForm(forms.ModelForm):
    class Meta:
        model = models.Race
        fields = ('name', 'plural_name')

    def clean_name(self):
        name = self.cleaned_data.get('name', '')

        try:
            name.encode('cp1252')
        except UnicodeEncodeError:
            raise forms.ValidationError(
                "Race name is restricted to the cp1252/latin1 character set.")

        return name

    def clean_plural_name(self):
        plural_name = self.cleaned_data.get('plural_name', '')

        try:
            plural_name.encode('cp1252')
        except UnicodeEncodeError:
            raise forms.ValidationError(
                "Race plural name is restricted to the"
                " cp1252/latin1 character set.")

        return plural_name

    def clean(self):
        cleaned_data = super(RaceForm, self).clean()
        game = self.instance.game
        r_id = self.instance.id

        name = cleaned_data.get('name', '')
        existing_race = models.Race.objects.filter(game=game, name=name)
        if existing_race and r_id != existing_race.get().id:
            raise forms.ValidationError(
                "The race name '{0}' is already being used for"
                " this game.".format(name))

        plural_name = cleaned_data.get('plural_name', '')
        existing_race = models.Race.objects.filter(game=game,
                                                   plural_name=plural_name)
        if existing_race and r_id != existing_race.get().id:
            raise forms.ValidationError(
                "The race plural_name '{0}' is already being used for"
                " this game.".format(plural_name))

        max_length = self.instance._meta.get_field('slug').max_length
        slug, num, end = slugify(plural_name), 1, ''
        if len(slug) > max_length:
            slug = slug[:max_length]

        while game.races.exclude(pk=r_id
                                 ).filter(slug=slug+end).exists():
            num += 1
            end = str(num)
            if len(slug) + len(end) > max_length:
                slug = slug[:max_length - len(end)]

        self.instance.slug = slug + end
        return cleaned_data


class ChooseUserRaceForm(forms.ModelForm):
    class Meta:
        model = models.Race
        fields = ('racefile',)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(ChooseUserRaceForm, self).__init__(*args, **kwargs)
        self.fields['racefile'].queryset = models.StarsFile.objects.filter(
            userrace__user=user
        )
        self.fields['racefile'].choices = [
            (u'', self.fields['racefile'].empty_label)
        ] + [
            (u.racefile.id, u.identifier)
            for u in models.UserRace.objects.filter(user=user,
                                                    racefile__isnull=False)
        ]


class AmbassadorForm(forms.ModelForm):
    class Meta:
        model = models.Ambassador
        exclude = ('race', 'user', 'active')


class RaceFileForm(forms.ModelForm):
    class Meta:
        model = models.StarsFile
        fields = ('file',)

    def clean_file(self):
        f = self.cleaned_data.get('file')

        valid = True
        try:
            self.stars_file = base.StarsFile()
            self.stars_file.bytes = f.read()
            if self.stars_file.type != 'r':
                valid = False
            elif self.stars_file.counts != {8: 1, 6: 1, 0: 1}:
                valid = False
        except (base.StarsError, Exception):
            valid = False

        if valid:
            self.instance.type = 'r'
        else:
            raise forms.ValidationError("Not a valid Stars race file.")

        return f


class UserRaceForm(forms.ModelForm):
    class Meta:
        model = models.UserRace
        fields = ('identifier',)


class OrderFileForm(forms.ModelForm):
    class Meta:
        model = models.StarsFile
        fields = ('file',)

    def clean_file(self):
        f = self.cleaned_data.get('file')

        try:
            self._sfile = models.StarsFile.parse(f.read(), type='x')
        except (base.StarsError, Exception):
            raise forms.ValidationError("Not a valid Stars order file.")

        self.instance.type = 'x'
        return f


class HistoryFileForm(forms.ModelForm):
    class Meta:
        model = models.StarsFile
        fields = ('file',)

    def clean_file(self):
        f = self.cleaned_data.get('file')

        try:
            self._sfile = models.StarsFile.parse(f.read(), type='h')
        except (base.StarsError, Exception):
            raise forms.ValidationError("Not a valid Stars history file.")

        self.instance.type = 'h'
        return f


class RacePageForm(forms.ModelForm):
    set_as_homepage = forms.BooleanField(required=False)

    class Meta:
        model = models.RacePage
        fields = ('title', 'body')
