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
        slug = cleaned_data.get('slug')

        if models.Race.objects.filter(game=game, slug=slug).exists():
            raise forms.ValidationError(
                "The race slug '{0}' is already being used for"
                " this game.".format(slug))

        return cleaned_data

class AmbassadorForm(forms.ModelForm):
    class Meta:
        model = models.Ambassador
        exclude = ('race', 'user', 'active')
