from django.conf import settings
from django import forms

from . import models


class CreateGameForm(forms.ModelForm):
    class Meta:
        model = models.Game
        exclude = ('description_html', 'host', 'created', 'state')


class RaceForm(forms.ModelForm):
    class Meta:
        model = models.Race
        fields = ('name', 'plural_name')

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

        return cleaned_data

class AmbassadorForm(forms.ModelForm):
    class Meta:
        model = models.Ambassador
        exclude = ('race', 'user', 'active')
