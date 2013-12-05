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
        except base.StarsError:
            valid = False

        if valid:
            self.instance.type = 'r'
        else:
            raise forms.ValidationError("Not a valid Stars race file.")

        return f
