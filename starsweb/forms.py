from django.conf import settings
from django import forms
from models import Game


optional_imports = {}

if 'micropress' in settings.INSTALLED_APPS:
    from micropress.forms import CreatePressForm
    optional_imports['pressform'] = CreatePressForm

if 'joinrequests' in settings.INSTALLED_APPS:
    from joinrequests.forms import AllowJoinForm
    optional_imports['joinform'] = AllowJoinForm


def additional_forms(data):
    return dict((name, form(data, prefix=name))
                for name, form in optional_imports.iteritems())


class CreateGameForm(forms.ModelForm):
    class Meta:
        model = Game
        exclude = ('description_html', 'host', 'created', 'state')
