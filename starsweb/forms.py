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
        exclude = ('game', 'player_number')

    def clean(self):
        cleaned_data = super(RaceForm, self).clean()
        game = self.instance.game
        r_id = self.instance.id
        slug = cleaned_data.get('slug')

        existing_race = models.Race.objects.filter(game=game, slug=slug)

        if existing_race and r_id != existing_race.get().id:
            raise forms.ValidationError(
                "The race slug '{0}' is already being used for"
                " this game.".format(slug))

        return cleaned_data

class AmbassadorForm(forms.ModelForm):
    class Meta:
        model = models.Ambassador
        exclude = ('race', 'user', 'active')
