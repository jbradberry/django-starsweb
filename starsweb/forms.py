from django.conf import settings
from django import forms

from . import models


class CreateGameForm(forms.ModelForm):
    class Meta:
        model = models.Game
        exclude = ('description_html', 'host', 'created', 'state')
