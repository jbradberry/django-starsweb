from django.template.defaultfilters import slugify
from django.conf import settings
from django import forms

from starslib import base

from . import models


class CreateGameForm(forms.ModelForm):
    class Meta:
        model = models.Game
        exclude = ('description_html', 'host', 'created', 'state')


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


class AmbassadorForm(forms.ModelForm):
    class Meta:
        model = models.Ambassador
        exclude = ('race', 'user', 'active')


class RaceFileForm(forms.ModelForm):
    class Meta:
        model = models.StarsFile
        fields = ('file',)

    def __init__(self, *args, **kwargs):
        super(RaceFileForm, self).__init__(*args, **kwargs)
        self.warnings = set()

    def clean_file(self):
        f = self.cleaned_data.get('file')

        valid = True
        try:
            stars_file = base.StarsFile()
            stars_file.bytes = f.read()
            if stars_file.type != 'r':
                valid = False
            elif stars_file.counts != {8: 1, 6: 1, 0: 1}:
                valid = False
        except base.StarsError:
            valid = False

        if valid:
            self.instance.type = 'r'

            race_struct = stars_file.structs[1]
            name = race_struct.race_name
            plural_name = race_struct.plural_race_name

            if name.strip() != name or plural_name.strip() != plural_name:
                self.warnings.add('extra-whitespace')
                name = name.strip()
                plural_name = plural_name.strip()

            name_bad = name.lower().startswith("the ")
            pname_bad = plural_name.lower().startswith("the ")
            if name_bad or pname_bad:
                self.warnings.add('prepended-the')
        else:
            raise forms.ValidationError("Not a valid Stars race file.")

        return f
